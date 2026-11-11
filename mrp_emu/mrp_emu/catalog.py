"""应用目录：MRP 头元数据解析、本地索引、在线索引 JSON 缓存与后台下载。

数据源
------
* 本地列表：扫描运行环境（workdir）下的 ``*.mrp``，只读每个文件的前 0xF0 字节
  就能拿到标题/厂商/描述/appid/版本（字段偏移见 docs/03-MRP包格式规范.md）。
* 在线列表：vmrp.github.io 仓库的 ``public/data.txt``（NDJSON，664 条站点自建索引）
  + ``public/mrps`` 目录清单。首次在后台线程拉一次，落盘成
  ``workdir/cache/online_index.json``，之后直接从缓存读，过期才刷新。
* 点在线列表项时按需下载单个 MRP 到 ``workdir/mythroad/`` —— 与 dsm 层的
  默认查找目录一致，下完即可直接 start_dsm()。

网络走系统代理（Clash 等会写进系统设置/环境变量）；连不上时会自动探测
几个常见本地代理端口。全程只用标准库，不引入 requests。
"""

from __future__ import annotations

import json
import os
import queue
import socket
import struct
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- 常量
REPO_RAW = "https://raw.githubusercontent.com/vmrp/vmrp.github.io/master/public"
REPO_API = "https://api.github.com/repos/vmrp/vmrp.github.io/contents/public/mrps?ref=master"
REPO_WEB = "https://github.com/vmrp/vmrp.github.io/tree/master/public"
DATA_URL = f"{REPO_RAW}/data.txt"
MRP_DIR_URL = f"{REPO_RAW}/mrps"

HDR_SIZE = 0xF0
SCHEMA = 1
DEFAULT_TTL = 7 * 24 * 3600        # 在线索引缓存有效期：7 天
LOCAL_PROXY_PORTS = (7890, 7897, 10809, 1080)
UA = {"User-Agent": "PymRP/1.0 (+https://github.com/Yichou/pymrp)"}

# 固定头字段表：偏移 -> (长度, 名字, 类型)
# 长度全部与官方《mythroad 工程文件编写指南》的字段上限一致：
#   appname 最多 23 有效字符 -> 24 字节；vendor 39 -> 40；description 63 -> 64；
#   filename 11 ASCII -> 12。
STR_FIELDS = (
    (0x10, 12, "filename"),
    (0x1C, 24, "title"),
    (0x34, 16, "auth"),
    (0x58, 40, "vendor"),
    (0x80, 64, "desc"),
)
U32_FIELDS = (
    (0x04, "file_start_minus8"),
    (0x08, "total_size"),
    (0x0C, "screen_width"),
    (0x44, "appid"),
    (0x48, "version"),
    (0x4C, "flag"),
    (0x50, "builder_version"),
    (0x54, "crc32"),
    (0xC8, "screen_width2"),
    (0xCC, "screen_height"),
    (0xD0, "plat"),
)


def _gbk(raw: bytes) -> str:
    """取 NUL 结尾的 GBK 字符串，丢掉控制字符和替换符。"""
    text = raw.split(b"\x00", 1)[0].decode("gbk", "replace")
    text = text.replace("\ufffd", "")
    return "".join(c for c in text if c == " " or c.isprintable()).strip()


def _u32(d: bytes, off: int) -> int:
    return struct.unpack_from("<I", d, off)[0] if len(d) >= off + 4 else 0


@dataclass
class MrpEntry:
    """MRP 包内的一个条目。"""

    name: str
    offset: int
    size: int                  # 压缩后大小
    rsv: int = 0

    @property
    def is_gzip(self) -> bool:
        return self.size >= 2


def read_mrp_entries(path: str | Path) -> list[MrpEntry]:
    """读出一个 MRP 的完整条目表。

    固定头 0xF0 之后是条目表，每项::

        u32 nameLen | name[nameLen] | u32 offset | u32 csize | u32 rsv

    最后一个条目是**包尾标记**（csize 固定为一个越界的大数），不是真实
    条目 —— 这里会把它剔除，避免释放时写出垃圾文件。
    """
    try:
        with open(path, "rb") as fh:
            d = fh.read()
    except OSError:
        return []
    if len(d) < HDR_SIZE or d[:4] != b"MRPG":
        return []
    size = len(d)
    out: list[MrpEntry] = []
    pos = HDR_SIZE
    while pos + 16 <= size:
        nl = _u32(d, pos)
        if not (2 <= nl <= 128):
            break
        if pos + 4 + nl + 12 > size:
            break
        raw = d[pos + 4:pos + 4 + nl]
        name = (raw[:-1] if raw[-1:] == b"\x00" else raw)
        name = name.decode("gbk", "replace")
        off, csz, rsv = struct.unpack_from("<III", d, pos + 4 + nl)
        pos += 4 + nl + 12
        # 包尾标记：偏移+大小越界
        if off + csz > size:
            continue
        out.append(MrpEntry(name, off, csz, rsv))
    return out


def read_mrp_entry_data(path: str | Path, entry: MrpEntry) -> bytes:
    """取出一个条目的内容；gzip 的自动解压。"""
    try:
        with open(path, "rb") as fh:
            fh.seek(entry.offset)
            blob = fh.read(entry.size)
    except OSError:
        return b""
    if blob[:2] == b"\x1f\x8b":
        try:
            return zlib.decompressobj(47).decompress(blob)
        except zlib.error:
            return blob
    return blob


def read_mrp_header(src: str | Path | bytes) -> dict:
    """读一个 MRP 的固定头（只读前 0xF0 字节），返回全部已确证字段。

    老版本 builder(10000) 的 auth/crc32 位置填的是特征码而非文本/校验值，
    因此 ``auth`` 只有在 ``builder_version >= 10002`` 时才置可信。
    """
    if isinstance(src, (str, Path)):
        with open(src, "rb") as fh:
            head = fh.read(HDR_SIZE)
    else:
        head = src[:HDR_SIZE]
    if len(head) < 0xE0 or head[:4] != b"MRPG":
        raise ValueError("不是有效的 MRP 文件（魔数不是 MRPG）")

    out = {name: _gbk(head[off:off + size]) for off, size, name in STR_FIELDS}
    out.update({name: _u32(head, off) for off, name in U32_FIELDS})
    out["appid_be"] = int.from_bytes(head[0xC0:0xC4], "big")
    out["version_be"] = int.from_bytes(head[0xC4:0xC8], "big")
    out["auth"] = out["auth"] if out["builder_version"] >= 10002 else ""
    out["valid"] = True
    return out


def probe_entry_ext(path: str | Path) -> str:
    """看包内条目表有没有 start.mr，决定 start_dsm() 的 ext 参数。

    实测（本地 14 个样本 + 在线抽样）：**所有** MRP 都用 ``start.mr`` 作入口，
    给普通应用传 ``cfunction.ext`` 会报 ``exit de is nil / init failed``。
    这里仍然读一次条目表，遇到不含 start.mr 的老包退回 cfunction.ext。
    """
    try:
        with open(path, "rb") as fh:
            d = fh.read(HDR_SIZE + 4096)
        pos, names = HDR_SIZE, []
        while pos + 16 <= len(d):
            nl = _u32(d, pos)
            if not (2 <= nl <= 64):
                break
            raw = d[pos + 4:pos + 4 + nl]
            if raw[-1:] != b"\x00":
                break
            names.append(raw[:-1].decode("ascii", "replace"))
            pos += 4 + nl + 12
        return "start.mr" if "start.mr" in names else "cfunction.ext"
    except (OSError, ValueError):
        return "start.mr"


def safe_run_name(path: str | Path) -> str:
    """返回 dsm/ext 能安全打开的运行文件名（不含目录）。

    ext 内部拼接路径用的是固定小缓冲，实测曲奇启动器把
    ``mythroad/冒泡6.0（线条模拟器提取（曲奇启动）.mrp``（GBK 41+ 字节）
    截成 ``mythroad/冒泡6.0（线条模拟器提取（曲奇启``，于是 ``mr_open``
    永远失败、包内 ``res_lang0.rc`` 报 ``code=2002``，连锁导致资源全缺。
    真机上这类应用用的是 MRP 头 0x10 处的 8.3 ASCII 短名（``cookie.mrp``）。

    短 ASCII 名原样返回；长名/中文名优先用包头声明的短名，
    包头不可读或不合法时退化为文件名散列，保证 ASCII 且不会被截断。
    """
    p = Path(path)
    raw = p.name.encode("gbk", "replace")
    if len(raw) <= 24 and all(b < 0x80 for b in raw):
        return p.name

    short = ""
    try:
        short = read_mrp_header(p).get("filename", "")
    except (OSError, ValueError):
        pass
    if (short and len(short) <= 24
            and all(c.isalnum() or c in "._-" for c in short)):
        return short if short.lower().endswith(".mrp") else short + ".mrp"

    import hashlib
    digest = hashlib.sha1(p.name.encode("utf-8", "replace")).hexdigest()[:8]
    return f"app{digest}.mrp"


@dataclass
class MrpMeta:
    """一条应用记录（本地/在线通用）。"""
    file: str
    title: str = ""
    vendor: str = ""
    desc: str = ""
    appid: int = 0
    version: int = 0
    size: int = 0
    width: int = 0
    source: str = "local"          # local | online
    path: str = ""                 # 本地绝对路径（已下载/本地文件）
    url: str = ""                  # 在线下载地址
    downloaded: bool = False       # 在线项是否已落到 mythroad/

    @property
    def label(self) -> str:
        return self.title or Path(self.file).stem

    @property
    def subtitle(self) -> str:
        bits = [self.vendor] if self.vendor else []
        if self.size:
            bits.append(f"{self.size / 1024:.0f}K")
        if self.version:
            bits.append(f"v{self.version}")
        return " · ".join(bits) or self.file

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MrpMeta":
        keys = {f for f in cls.__dataclass_fields__}  # noqa: C416
        return cls(**{k: v for k, v in d.items() if k in keys})


def meta_from_file(path: str | Path) -> MrpMeta | None:
    """从本地 .mrp 生成一条记录；解析失败时退回文件名，不抛异常。"""
    p = Path(path)
    try:
        h = read_mrp_header(p)
    except (OSError, ValueError):
        return None
    return MrpMeta(
        file=p.name,
        title=h["title"] or p.stem,
        vendor=h["vendor"],
        desc=h["desc"],
        appid=h["appid"],
        version=h["version"],
        size=p.stat().st_size,
        width=h["screen_width"],
        source="local",
        path=str(p.resolve()),
        downloaded=True,
    )


def meta_from_db(row: dict, sizes: dict[str, int] | None = None) -> MrpMeta:
    """把 data.txt 的一行（站点索引）转成记录。"""
    name = row.get("file") or (str(row.get("FileName", "")) + ".mrp")
    sizes = sizes or {}
    return MrpMeta(
        file=name,
        title=str(row.get("DisplayName") or row.get("FileName") or Path(name).stem),
        vendor=str(row.get("Vendor") or ""),
        desc=str(row.get("Desc") or ""),
        appid=int(row.get("Appid") or 0),
        version=int(row.get("Version") or 0),
        size=int(sizes.get(name.lower()) or row.get("MrpTotalLen") or 0),
        width=int(row.get("ScreenWidth") or 0),
        source="online",
        url=f"{MRP_DIR_URL}/{urllib.parse.quote(name)}",
        downloaded=False,
    )


# ---------------------------------------------------------------- 网络
class Net:
    """极简 HTTP 客户端：系统代理 + 自动探测常见本地代理端口 + 失败重试。"""

    def __init__(self, proxy: str | None = None, timeout: float = 20.0,
                 log=print) -> None:
        self.log = log
        self.timeout = timeout
        self._explicit = proxy or os.environ.get("PYMRP_PROXY") or ""
        self._probed: str | None = None
        self._opener = self._make(self._effective_proxy())

    def _effective_proxy(self) -> dict:
        if self._explicit:
            return {"http": self._explicit, "https": self._explicit}
        if self._probed:
            return {"http": "http://127.0.0.1:" + str(self._probed),
                    "https": "http://127.0.0.1:" + str(self._probed)}
        return urllib.request.getproxies()

    def _make(self, proxies: dict) -> urllib.request.OpenerDirector:
        return urllib.request.build_opener(urllib.request.ProxyHandler(proxies))

    def _probe(self) -> bool:
        """直连失败后，探一下本机常见代理端口；成功就固定用它。"""
        if self._explicit or self._probed:
            return False
        for port in LOCAL_PROXY_PORTS:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                    pass
            except OSError:
                continue
            self._probed = port
            self._opener = self._make(self._effective_proxy())
            self.log(f"[net] 检测到本地代理 127.0.0.1:{port}")
            return True
        return False

    def get(self, url: str, extra_headers: dict | None = None) -> bytes:
        headers = dict(UA)
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(url, headers=headers)
        last: Exception | None = None
        for attempt in range(2):
            try:
                with self._opener.open(req, timeout=self.timeout) as resp:
                    return resp.read()
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                last = exc
                if attempt == 0 and self._probe():
                    continue
                break
        raise RuntimeError(f"网络请求失败: {url} ({last})")


def fetch_online(net: Net) -> list[MrpMeta]:
    """拉 data.txt + 目录清单，合并成在线列表。"""
    raw = net.get(DATA_URL)
    rows = []
    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not rows:
        raise RuntimeError("data.txt 为空或格式不对")

    # 目录清单只用来补准文件大小；拿不到也不影响主流程
    sizes: dict[str, int] = {}
    try:
        listing = json.loads(net.get(
            REPO_API, {"Accept": "application/vnd.github+json"}).decode("utf-8"))
        sizes = {x["name"].lower(): int(x.get("size") or 0)
                 for x in listing if x.get("type") == "file"
                 and x.get("name", "").lower().endswith(".mrp")}
    except Exception as exc:  # noqa: BLE001 - 目录清单是可选增强
        net.log(f"[net] 目录清单不可用（改用 data.txt 里的长度）: {exc}")

    items = [meta_from_db(r, sizes) for r in rows if r.get("file")]
    items.sort(key=lambda m: m.label)
    return items


# ---------------------------------------------------------------- 目录
class Catalog:
    """本地 + 在线两个列表，所有耗时操作都放到后台线程。

    主线程每帧调 ``poll()`` 拿事件；线程内部状态用锁保护，UI 可以直接读
    ``online_state`` / ``progress`` 这类字段（读的是不可变小对象，天然安全）。
    """

    def __init__(self, workdir: str | Path, cache_dir: str | Path | None = None,
                 download_dir: str | Path | None = None, proxy: str | None = None,
                 ttl: int = DEFAULT_TTL, log=print) -> None:
        self.workdir = Path(workdir).resolve()
        self.cache_dir = Path(cache_dir) if cache_dir else self.workdir / "cache"
        # dsm 侧默认在 <workdir>/mythroad/ 下找 mrp（见 VirtualFs 的 c: 前缀）
        self.download_dir = (Path(download_dir) if download_dir
                             else self.workdir / "mythroad")
        self.ttl = ttl
        self.log = log
        self.net = Net(proxy=proxy, log=log)

        self.online_file = self.cache_dir / "online_index.json"
        self.local_file = self.cache_dir / "local_index.json"
        self.online_items: list[MrpMeta] = []
        self.local_items: list[MrpMeta] = []
        self.online_state = "idle"        # idle | loading | ready | error
        self.online_message = "尚未加载"
        self.fetched_at = ""
        self.progress: dict[str, dict] = {}   # file -> {state, done, total, error, path}
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._refreshing = False

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.download_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            # 工作目录只读时退到用户目录（同时提示：下载的文件仍需手动放进运行环境）
            self.log(f"[catalog] {exc}，缓存改用用户目录")
            base = Path.home() / ".pymrp"
            self.cache_dir = base / "cache"
            self.download_dir = base / "mrps"
            self.online_file = self.cache_dir / "online_index.json"
            self.local_file = self.cache_dir / "local_index.json"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.download_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ 本地
    def scan_local(self, force: bool = False) -> list[MrpMeta]:
        """扫描 workdir 下全部 .mrp（跳过 cache 目录），写 local_index.json。"""
        if not force and self.local_items:
            return self.local_items
        items: list[MrpMeta] = []
        seen: set[str] = set()
        for p in sorted(self.workdir.rglob("*.mrp")):
            if self.cache_dir in p.parents:
                continue
            if p.name.lower() in seen:
                continue
            m = meta_from_file(p)
            if m is None:
                continue
            seen.add(p.name.lower())
            items.append(m)
        # 下载目录在 workdir 之外时（只读回退），也要算进本地列表
        if self.workdir not in self.download_dir.parents and self.download_dir.is_dir():
            for p in sorted(self.download_dir.glob("*.mrp")):
                if p.name.lower() in seen:
                    continue
                m = meta_from_file(p)
                if m:
                    seen.add(p.name.lower())
                    items.append(m)
        items.sort(key=lambda x: x.label)
        self._mark_downloaded(items)
        with self._lock:
            self.local_items = items
        self._write_json(self.local_file, {
            "schema": SCHEMA, "generated_at": _now(), "root": str(self.workdir),
            "count": len(items), "items": [m.to_dict() for m in items],
        })
        return items

    def _mark_downloaded(self, items: list[MrpMeta]) -> None:
        online = {m.file.lower(): m for m in self.online_items}
        for m in items:
            hit = online.get(m.file.lower())
            if hit:
                hit.downloaded = True
                hit.path = m.path
                hit.size = m.size or hit.size

    # ------------------------------------------------------------ 在线缓存
    def _known_local_files(self) -> dict[str, Path]:
        """一次扫描收集运行环境下所有 mrp 文件名 → 路径。"""
        out: dict[str, Path] = {}
        for base in (self.download_dir, self.workdir / "mythroad", self.workdir):
            if not base.is_dir():
                continue
            for p in base.glob("*.mrp"):
                out.setdefault(p.name.lower(), p)
        return out

    def _read_online_cache(self) -> bool:
        try:
            d = json.loads(self.online_file.read_text("utf-8"))
        except (OSError, ValueError):
            return False
        if d.get("schema") != SCHEMA or not d.get("items"):
            return False
        self.online_items = [MrpMeta.from_dict(x) for x in d["items"]]
        self.fetched_at = d.get("fetched_at", "")
        known = self._known_local_files()
        for m in self.online_items:            # 已下载状态以磁盘为准，不信旧缓存
            p = known.get(m.file.lower())
            m.downloaded = p is not None
            m.path = str(p) if p else ""
        self.online_state = "ready"
        self.online_message = f"缓存 {len(self.online_items)} 个应用"
        return True

    def _cache_age(self) -> float:
        try:
            t = datetime.fromisoformat(self.fetched_at)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - t).total_seconds()
        except (ValueError, TypeError):
            return float("inf")

    def start_refresh(self, force: bool = False) -> None:
        """首次进入游戏中心时调用：缓存新鲜就直接用，否则后台拉。"""
        with self._lock:
            if self._refreshing:
                return
            if not self.online_items:
                self._read_online_cache()      # 先把上次落盘的 JSON 读进来
            if (self.online_items and not force and self._cache_age() < self.ttl):
                # 纯读本地 JSON 缓存，不弹通知（避免每次开机都盖住桌面）
                self._events.put(("online_cached", len(self.online_items)))
                return
            self._refreshing = True
            self.online_state = "loading"
            self.online_message = "正在后台获取在线列表…"
        threading.Thread(target=self._refresh_worker, kwargs={"force": force},
                         daemon=True, name="pymrp-online-index").start()

    def _refresh_worker(self, force: bool) -> None:
        try:
            items = fetch_online(self.net)
            known = self._known_local_files()
            for m in items:
                f = known.get(m.file.lower())
                if f:
                    m.downloaded = True
                    m.path = str(f)
            with self._lock:
                self.online_items = items
                self.fetched_at = _now()
                self.online_state = "ready"
                self.online_message = f"{len(items)} 个在线应用"
                self._refreshing = False
            self._write_json(self.online_file, {
                "schema": SCHEMA, "source": REPO_WEB, "fetched_at": self.fetched_at,
                "count": len(items), "items": [m.to_dict() for m in items],
            })
            self.log(f"[catalog] 在线索引已缓存 {len(items)} 条 -> {self.online_file}")
            self._events.put(("online_ready", len(items)))
            self.scan_local(force=True)
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._refreshing = False
                ok = bool(self.online_items)
                self.online_state = "ready" if ok else "error"
                self.online_message = (f"刷新失败，使用旧缓存：{exc}" if ok
                                       else f"获取失败：{exc}")
            self._events.put(("online_error", str(exc)))

    # ------------------------------------------------------------ 下载
    def find_local_file(self, name: str) -> Path | None:
        """按文件名找已经落到运行环境里的 mrp。"""
        for base in (self.download_dir, self.workdir / "mythroad", self.workdir):
            p = base / name
            if p.is_file() and p.stat().st_size > HDR_SIZE:
                with open(p, "rb") as fh:
                    if fh.read(4) == b"MRPG":
                        return p
        return None

    def start_download(self, item: MrpMeta) -> None:
        """后台下载单个 MRP；已存在则直接发 ready 事件。"""
        existing = self.find_local_file(item.file)
        if existing:
            item.downloaded = True
            item.path = str(existing)
            self._set_progress(item.file, state="ready", done=item.size,
                               total=item.size, path=str(existing))
            self._events.put(("download_ready", item.file))
            return
        if self.progress.get(item.file, {}).get("state") == "downloading":
            return
        self._set_progress(item.file, state="downloading", done=0,
                           total=item.size, error="")
        threading.Thread(target=self._download_worker, args=(item,),
                         daemon=True, name="pymrp-download").start()

    def _download_worker(self, item: MrpMeta) -> None:
        url = item.url or f"{MRP_DIR_URL}/{urllib.parse.quote(item.file)}"
        part = self.download_dir / (item.file + ".part")
        try:
            req = urllib.request.Request(url, headers=dict(UA))
            with self.net._opener.open(req, timeout=self.net.timeout) as resp:
                total = int(resp.headers.get("Content-Length") or item.size or 0)
                done = 0
                with open(part, "wb") as fh:
                    while True:
                        chunk = resp.read(16384)
                        if not chunk:
                            break
                        fh.write(chunk)
                        done += len(chunk)
                        self._set_progress(item.file, state="downloading",
                                           done=done, total=total or item.size)
            with open(part, "rb") as check:
                magic = check.read(4)
            if done < HDR_SIZE or magic != b"MRPG":
                raise RuntimeError("下载内容不是有效 MRP（可能被代理拦截）")
            target = self.download_dir / item.file
            part.replace(target)
            item.downloaded = True
            item.path = str(target)
            self._set_progress(item.file, state="ready", done=done,
                               total=total or done, path=str(target))
            self.log(f"[catalog] 已下载 {item.file} ({done} 字节) -> {target}")
            self._events.put(("download_ready", item.file))
            self.scan_local(force=True)
        except Exception as exc:  # noqa: BLE001
            try:
                part.unlink(missing_ok=True)
            except OSError:
                pass
            self._set_progress(item.file, state="error", error=str(exc))
            self._events.put(("download_error", (item.file, str(exc))))

    def _set_progress(self, key: str, **kw) -> None:
        with self._lock:
            cur = dict(self.progress.get(key, {}))
            cur.update(kw)
            self.progress[key] = cur

    def get_progress(self, key: str) -> dict:
        with self._lock:
            return dict(self.progress.get(key, {}))

    # ------------------------------------------------------------ 事件
    def poll(self) -> list[tuple[str, object]]:
        out = []
        while True:
            try:
                out.append(self._events.get_nowait())
            except queue.Empty:
                return out

    def _write_json(self, path: Path, payload: dict) -> None:
        # 扫描与刷新可能在两个线程里同时写，用唯一临时名 + 锁避免互相覆盖
        with self._write_lock:
            tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                               "utf-8")
                tmp.replace(path)
            except OSError as exc:
                print(f"[catalog] 写缓存失败 {path}: {exc}")
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- CLI 自检
def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(description="MRP 应用目录：解析 / 索引 / 下载")
    p.add_argument("cmd", choices=("head", "scan", "refresh", "get"))
    p.add_argument("target", nargs="?")
    p.add_argument("--workdir", default="runtime")
    p.add_argument("--proxy")
    p.add_argument("--force", action="store_true")
    a = p.parse_args(argv)

    if a.cmd == "head":
        if not a.target:
            print("需要 .mrp 路径", file=sys.stderr)
            return 2
        print(json.dumps(read_mrp_header(a.target), ensure_ascii=False, indent=2))
        return 0

    cat = Catalog(a.workdir, proxy=a.proxy)
    if a.cmd == "scan":
        items = cat.scan_local(force=a.force)
        for m in items:
            print(f"{m.label:<20} | {m.vendor:<12} | {m.size:>8} | {m.file}")
        print(f"共 {len(items)} 条 -> {cat.local_file}")
    elif a.cmd == "refresh":
        cat.start_refresh(force=a.force)
        while cat.online_state == "loading":
            for ev in cat.poll():
                print("event:", ev)
            time.sleep(0.1)
        print(cat.online_state, cat.online_message)
        for m in cat.online_items[:10]:
            print(f"{m.label:<24} | {m.vendor:<12} | {m.size:>8} | {m.file}")
        print(f"共 {len(cat.online_items)} 条 -> {cat.online_file}")
    elif a.cmd == "get":
        if not a.target:
            print("需要文件名", file=sys.stderr)
            return 2
        cat.start_refresh()
        while cat.online_state == "loading":
            time.sleep(0.1)
        hit = next((m for m in cat.online_items if m.file == a.target), None)
        if hit is None:
            print("在线列表里没有", a.target)
            return 1
        cat.start_download(hit)
        while cat.get_progress(a.target).get("state") == "downloading":
            print("\r", cat.get_progress(a.target), end="", flush=True)
            time.sleep(0.15)
        print("\n", cat.get_progress(a.target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
