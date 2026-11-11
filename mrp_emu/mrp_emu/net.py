"""MRP 网络模块（宿主侧）。

参考三份实现，语义以它们为准：

* ``mrpoid/libm/src/main/jni/src/network.c`` —— socket 状态机、10 个槽位、
  cmwap ``10.0.0.172`` 代理、非阻塞 connect/select、send/recv 返回值；
* ``vmrp/dl_bridge.c`` + ``dl_dsm.h`` —— ``dsm_require_funcs`` 的 11 个
  网络槽位签名，以及 ``NETWORK_CB = int32 (*)(int32 result, void *userData)``
  回调要用 ``bridge_dsm_network_cb``（手动切 r9）来触发；
* ``mr/mrporting.h`` —— ``MR_SOCK_*`` / ``MR_SOCKET_*`` / ``MR_IPPROTO_*``
  枚举值，以及 ``mr_getHostByName`` 返回的是**主机序 u32 IP**。

IP 的字节序是这套接口最容易踩错的地方：``mr_connect(s, ip, port, type)``
里的 ``ip`` 是 ``a<<24 | b<<16 | c<<8 | d``（表示 ``a.b.c.d``），
mrpoid 用 ``htonl(ip)`` 填 ``sin_addr``，等价于这里的 ``u32_to_ip`` + inet_aton。

回调不能在 Unicorn 的 ``emu_start()`` 内部重入，所以全部排进队列，
由主循环每帧调 ``NetEngine.poll()`` 用 ``vm.call_arm()`` 执行。
"""

from __future__ import annotations

import errno
import queue
import re
import select
import socket
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .consts import MR_FAILED, MR_SUCCESS, MR_WAITING

# ---------------------------------------------------------------- 常量
MR_SOCK_STREAM = 0
MR_SOCK_DGRAM = 1
MR_IPPROTO_TCP = 0
MR_IPPROTO_UDP = 1
MR_SOCKET_BLOCK = 0
MR_SOCKET_NONBLOCK = 1

DSM_SOC_CLOSE = 0
DSM_SOC_OPEN = 1
DSM_SOC_CONNECTING = 2
DSM_SOC_CONNECTED = 3
DSM_SOC_ERR = 4

DSM_SOC_NOREAD = 0
DSM_SOC_READABLE = 1
DSM_SOC_NOWRITE = 0
DSM_SOC_WRITEABLE = 1

DSM_SUPPROT_SOC_NUM = 10          # dsm.h 里的拼写（原文如此），别"修正"
CMWAP_PROXY_IP = 0x0A0000AC       # 10.0.0.172 移动 cmwap 网关

# 斯凯官方域名早已被重新解析/停放，open-skyengine/skyengine-v2 的做法是
# 把这批老域名覆写到他们复刻的服务端 159.75.119.124（mrp.jysafe.cn 同机）。
# 格式与 v2 的 --dns-map 一致：SOURCE->IPv4[:PORT];...
# 传空字符串可清空；SOURCE 也可以是点分 IP，用来覆盖 cmwap 网关。
#
# 清单对齐 skyengine-v2 的 e2e 用例（test/e2e/dota/download-plugin.test.ts、
# test/e2e/optwar/speed.test.ts 等）：浏览器插件链会访问 proxy.51mrp.com /
# proxy2.51mrp.com 下载组件（brwmain/brwshell/embrw 等），缺了这两条
# 映射插件组件就下载不下来，表现为「插件打开后立刻退到主界面」。
DEFAULT_DNS_MAP = (
    "rop.skymobiapp.com->159.75.119.124;"
    "spd.skymobiapp.com->159.75.119.124;"
    "proxy.51mrp.com->159.75.119.124;"
    "proxy2.51mrp.com->159.75.119.124;"
    "wap.skmeg.com->159.75.119.124"
)

_HOST_RE = re.compile(rb"(?:X-Online-Host|Host)\s*:\s*([^\r\n]+)", re.IGNORECASE)


@dataclass(frozen=True)
class DnsMapping:
    source: str                  # 老域名或点分 IP，已小写、去尾点
    address: str                 # 目标 IPv4
    port: int | None = None      # 可选端口覆写


def parse_dns_map(text: str | None) -> list[DnsMapping]:
    """解析 ``host->ip[:port];host2->ip2``（语义对齐 skyengine-v2）。

    ``None`` 表示用内置默认表；空字符串表示完全不覆写。
    """
    if text is None:
        text = DEFAULT_DNS_MAP
    out: list[DnsMapping] = []
    seen: set[str] = set()
    for item in text.split(";"):
        item = item.strip()
        if not item:
            continue
        if "->" not in item:
            raise ValueError(f"DNS 映射格式错误: {item!r}，应为 HOST->IPv4[:PORT]")
        src, dst = (x.strip() for x in item.split("->", 1))
        src = src.rstrip(".").lower()
        if not src or src in seen:
            raise ValueError(f"DNS 映射源为空或重复: {src!r}")
        if ":" in dst:
            addr, _, p = dst.rpartition(":")
            try:
                port = int(p)
            except ValueError as exc:
                raise ValueError(f"DNS 映射端口无效: {item!r}") from exc
            if not 0 < port < 65536:
                raise ValueError(f"DNS 映射端口越界: {item!r}")
        else:
            addr, port = dst, None
        try:
            octets = [int(x) for x in addr.split(".")]
            valid = len(octets) == 4 and all(0 <= x <= 255 for x in octets)
        except ValueError:
            valid = False
        if not valid:
            raise ValueError(f"DNS 映射目标不是 IPv4: {item!r}")
        seen.add(src)
        out.append(DnsMapping(src, addr, port))
    return out

# 切应用会重建 App/NetEngine，但 DNS 线程池全局共用，避免每次新建线程。
_DNS_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mrp-dns")


def u32_to_ip(value: int) -> str:
    """``0x0A0000AC`` -> ``"10.0.0.172"``（与 network.c 的 ip2str 一致）。"""
    v = value & 0xFFFFFFFF
    return f"{(v >> 24) & 0xFF}.{(v >> 16) & 0xFF}.{(v >> 8) & 0xFF}.{v & 0xFF}"


def ip_to_u32(text: str) -> int:
    """``"10.0.0.172"`` -> ``0x0A0000AC``。"""
    parts = text.strip().split(".")
    if len(parts) != 4:
        return 0
    try:
        a, b, c, d = (int(x) & 0xFF for x in parts)
    except ValueError:
        return 0
    return (a << 24) | (b << 16) | (c << 8) | d


def parse_host(data: bytes) -> str:
    """从 HTTP 请求里抠真实主机（cmwap 代理用），兼容 ``X-Online-Host``。"""
    m = _HOST_RE.search(data)
    if not m:
        return ""
    host = m.group(1).decode("ascii", "replace").strip()
    # 去掉可能的路径/协议前缀
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0].strip()
    return host


def split_host_port(host: str) -> tuple[str, int]:
    if ":" in host:
        name, _, port = host.rpartition(":")
        try:
            return name, int(port) or 80
        except ValueError:
            return host, 80
    return host, 80


def parse_proxy_request(data: bytes) -> tuple[str, int, str, bytes] | None:
    """解析 cmwap 网关收到的首个请求，返回 ``(host, port, mode, outbound)``。

    对齐 skyengine-v2 ``wap_proxy.rs::parse_request``：

    * ``CONNECT host:port``       -> mode=connect，代理自己回 200，首包不转发；
    * ``GET http://host/path``    -> mode=absolute，改写成 origin-form、
      剥掉 ``Proxy-Connection``、必要时补 ``Host``；
    * ``POST /path`` + ``Host``   -> mode=host，原样转发。

    ``outbound`` 是应当写给真实服务器的字节（含原始 body）。
    """
    end = data.find(b"\r\n\r\n")
    head = data[:end] if end >= 0 else data
    body = data[end + 4:] if end >= 0 else b""
    lines = head.split(b"\r\n")
    if not lines or not lines[0]:
        return None
    parts = lines[0].decode("latin1").split(" ")
    if len(parts) != 3:
        return None
    method, target, version = parts
    if not version.startswith("HTTP/1."):
        return None

    headers: list[bytes] = []
    host_header = ""
    has_host = False
    for line in lines[1:]:
        if not line:
            continue
        name, _, value = line.partition(b":")
        key = name.decode("ascii", "replace").strip().lower()
        val = value.decode("latin1").strip()
        if key in ("host", "x-online-host"):
            has_host = True
            if not host_header:
                host_header = val
        if key != "proxy-connection":
            headers.append(line)

    if method.upper() == "CONNECT":
        host, port = split_host_port(target)
        return (host, port, "connect", body) if host else None

    if target.lower().startswith("http://"):
        rest = target[7:]
        cut = [i for i in (rest.find("/"), rest.find("?")) if i >= 0]
        idx = min(cut) if cut else len(rest)
        authority = rest[:idx]
        path = rest[idx:] or "/"
        if path.startswith("?"):
            path = "/" + path
        host, port = split_host_port(authority)
        if not host:
            return None
        out = f"{method} {path} {version}\r\n".encode("latin1")
        if headers:
            out += b"\r\n".join(headers) + b"\r\n"
        if not has_host:
            out += f"Host: {authority}\r\n".encode("latin1")
        out += b"\r\n" + body
        return host, port, "absolute", out

    if host_header:
        host, port = split_host_port(host_header)
        return (host, port, "host", data) if host else None
    return None


@dataclass
class SocketSlot:
    """对应 network.c 的 ``T_DSM_SOC_STAT``。"""

    sock: socket.socket | None = None
    state: int = DSM_SOC_CLOSE
    read_stat: int = DSM_SOC_NOREAD
    write_stat: int = DSM_SOC_NOWRITE
    sock_type: int = MR_SOCK_STREAM
    is_proxy: bool = False          # 目标是 10.0.0.172，等 send 时才知道真主机
    real_connected: bool = False
    host: str = ""
    connect_at: float = 0.0
    peer: tuple[str, int] = field(default_factory=lambda: ("", 0))
    # 内置 WAP 代理用：首包改写缓冲、CONNECT 隧道标志、代理自己生成的响应
    first_rewrite: bytes | None = None
    tunnel: bool = False
    pending_recv: bytearray = field(default_factory=bytearray)

    def reset(self) -> None:
        self.sock = None
        self.state = DSM_SOC_CLOSE
        self.read_stat = DSM_SOC_NOREAD
        self.write_stat = DSM_SOC_NOWRITE
        self.sock_type = MR_SOCK_STREAM
        self.is_proxy = False
        self.real_connected = False
        self.host = ""
        self.connect_at = 0.0
        self.peer = ("", 0)
        self.first_rewrite = None
        self.tunnel = False
        self.pending_recv.clear()


class NetEngine:
    """一套 socket 状态机 + DNS + ARM 异步回调。每个 App 一个实例。"""

    def __init__(self, vm, log=print, enabled: bool = True,
                 http_proxy: str = "", connect_timeout: float = 8.0,
                 dns_timeout: float = 4.0, dns_map: str | None = None,
                 wap_proxy: bool = True) -> None:
        self.vm = vm
        self.log = log
        self.enabled = enabled
        self.http_proxy = http_proxy.strip()
        self.connect_timeout = connect_timeout
        self.dns_timeout = dns_timeout
        # 老斯凯域名覆写表；wap_proxy=False 时 10.0.0.172 不再由内置代理接管，
        # 需要在 dns_map 里显式写 "10.0.0.172->IP[:PORT]"（对齐 skyengine-v2）。
        self.dns_map = parse_dns_map(dns_map)
        self.wap_proxy = wap_proxy
        self.slots = [SocketSlot() for _ in range(DSM_SUPPROT_SOC_NUM)]
        self.initialized = False
        self.mode = ""
        self.dns_cache: dict[str, int] = {}
        self._callbacks: queue.Queue[tuple[int, int, int]] = queue.Queue()
        self._dns_pool = _DNS_POOL
        self._lock = threading.Lock()
        # 统计，便于 --stats 与自检
        self.stats = {"socket": 0, "connect": 0, "send": 0, "send_bytes": 0,
                      "recv": 0, "recv_bytes": 0, "dns": 0, "callbacks": 0,
                      "errors": 0}

    # ------------------------------------------------------------ 工具
    def _mem(self):
        return self.vm.mem

    def _read(self, addr: int, length: int) -> bytes:
        mem = self._mem()
        n = max(0, min(int(length), 1 << 20))
        if not addr or n <= 0 or not mem.valid(addr, 1):
            return b""
        n = min(n, mem.base + mem.size - addr)
        return mem.read(addr, n) if n > 0 else b""

    def _write(self, addr: int, data: bytes) -> bool:
        mem = self._mem()
        if not addr or not data or not mem.valid(addr, len(data)):
            return False
        mem.write(addr, data)
        return True

    def _slot(self, s: int) -> SocketSlot | None:
        if 0 <= s < DSM_SUPPROT_SOC_NUM:
            return self.slots[s]
        return None

    def find_mapping(self, source: str) -> DnsMapping | None:
        """按老域名（或点分 IP）查覆写表，大小写不敏感、忽略尾点。"""
        key = (source or "").strip().rstrip(".").lower()
        if not key:
            return None
        for m in self.dns_map:
            if m.source == key:
                return m
        return None

    def resolve_target(self, host: str, port: int) -> tuple[str, int]:
        """把 MRP 以为的目标换成真实目标；映射端口优先于请求端口。"""
        m = self.find_mapping(host)
        if m:
            return m.address, (m.port if m.port is not None else port)
        return host, port

    def _queue_callback(self, cb: int, result: int, user_data: int = 0) -> None:
        # 0 / 明显不是模拟内存里的代码地址，就不要尝试跳进去
        if not cb or not self._mem().valid(cb, 4):
            return
        self._callbacks.put((cb & 0xFFFFFFFE, result & 0xFFFFFFFF,
                             user_data & 0xFFFFFFFF))

    # ------------------------------------------------------------ 生命周期
    def init_network(self, cb: int, mode: str, user_data: int = 0) -> int:
        """``initNetwork(NETWORK_CB cb, const char *mode, void *userData)``。

        mrpoid 直接返回 ``MR_SUCCESS``；vmrp 的 ext 可能等异步回调，
        所以这里两件事都做：立刻返回成功 + 排一个成功回调。
        MRP 侧 ``mr_initNetworkCB`` 只是把 socket.state 设成 CONNECTED，
        与直接用返回值的结果一致，重复一次无害。
        """
        self.close_network()
        self.mode = mode or ""
        self.initialized = True
        self.log(f"[net] initNetwork(mode={self.mode!r})")
        self._queue_callback(cb, MR_SUCCESS, user_data)
        return MR_SUCCESS

    def close_network(self) -> int:
        for s in self.slots:
            if s.sock is not None:
                try:
                    s.sock.close()
                except OSError:
                    pass
            s.reset()
        while not self._callbacks.empty():
            try:
                self._callbacks.get_nowait()
            except queue.Empty:
                break
        self.initialized = False
        return MR_SUCCESS

    def shutdown(self) -> None:
        # 只清 socket 状态；DNS 池是全局共享的，不在这里关
        self.close_network()

    def poll(self) -> None:
        """主循环每帧调用：把排队的 ARM 回调执行掉（不能在 emu_start 内重入）。"""
        if not self.vm:
            return
        for _ in range(8):           # 一帧最多 8 个，避免饿死渲染
            try:
                cb, result, user_data = self._callbacks.get_nowait()
            except queue.Empty:
                break
            try:
                self.vm.call_arm(cb, result, user_data)
                self.stats["callbacks"] += 1
            except Exception as exc:  # noqa: BLE001 - 回调崩了不能带崩模拟器
                self.stats["errors"] += 1
                self.log(f"[net] 回调 0x{cb:X} 异常: {exc}")

    # ------------------------------------------------------------ DNS
    def get_host_by_name(self, name: str, cb: int = 0, user_data: int = 0) -> int:
        """``getHostByName(const char *ptr, NETWORK_CB cb, void *userData)``。

        MRP 侧 ``_mr_getHost`` 直接把**返回值**写进 ``socket.ip``，所以必须
        同步返回 IP；同时排一个回调，兼容按异步方式写的 ext。
        """
        host = (name or "").strip()
        if not host:
            return MR_FAILED
        self.stats["dns"] += 1
        # 斯凯老域名先走覆写表：官方 DNS 早已被重新解析/停放，
        # 直接 getHostByName 会拿到错误的 IP（实测 38.48.128.189）。
        mapped = self.find_mapping(host)
        if mapped:
            result = ip_to_u32(mapped.address)
            self.dns_cache[host] = result
            self.log(f"[net] DNS {host} -> {mapped.address} (dns-map)")
            self._queue_callback(cb, result, user_data)
            return result
        # 本身是点分十进制就不用查 DNS
        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", host):
            result = ip_to_u32(host)
        else:
            result = self.dns_cache.get(host, 0)
            if not result:
                try:
                    fut = self._dns_pool.submit(socket.gethostbyname, host)
                    ip = fut.result(timeout=self.dns_timeout)
                    result = ip_to_u32(ip)
                except Exception as exc:  # noqa: BLE001
                    self.log(f"[net] DNS 失败 {host}: {exc}")
                    result = MR_FAILED
            if result > 0:
                self.dns_cache[host] = result
        self.log(f"[net] DNS {host} -> {u32_to_ip(result) if result > 0 else 'FAILED'}")
        self._queue_callback(cb, result, user_data)
        return result

    # ------------------------------------------------------------ socket
    def socket(self, sock_type: int, protocol: int = 0) -> int:
        if not self.enabled:
            return MR_FAILED
        with self._lock:
            idx = next((i for i, s in enumerate(self.slots)
                        if s.state == DSM_SOC_CLOSE), -1)
            if idx < 0:
                self.log("[net] socket 槽位已满 (10)")
                return MR_FAILED
            slot = self.slots[idx]
            if slot.sock is not None:
                try:
                    slot.sock.close()
                except OSError:
                    pass
                slot.reset()
            try:
                kind = socket.SOCK_DGRAM if sock_type == MR_SOCK_DGRAM else socket.SOCK_STREAM
                sock = socket.socket(socket.AF_INET, kind)
                sock.setblocking(False)
                if kind == socket.SOCK_STREAM:
                    try:
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    except OSError:
                        pass
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    except OSError:
                        pass
            except OSError as exc:
                self.log(f"[net] socket() 失败: {exc}")
                return MR_FAILED
            slot.sock = sock
            slot.sock_type = MR_SOCK_DGRAM if sock_type == MR_SOCK_DGRAM else MR_SOCK_STREAM
            slot.state = DSM_SOC_OPEN
            if slot.sock_type == MR_SOCK_DGRAM:
                slot.read_stat = DSM_SOC_READABLE
                slot.write_stat = DSM_SOC_WRITEABLE
            self.stats["socket"] += 1
            self.log(f"[net] socket(type={sock_type}) -> {idx}")
            return idx

    def _free_index(self) -> int:
        return next((i for i, s in enumerate(self.slots)
                     if s.state == DSM_SOC_CLOSE), -1)

    def _dial(self, slot: SocketSlot, host: str, port: int,
              blocking: bool) -> int:
        """建立一条真实 TCP 连接（可选走 HTTP CONNECT 出站代理）。"""
        old = slot.sock
        rc = 0
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target = (host, port)
            if self.http_proxy:
                p = split_host_port(self.http_proxy.replace("http://", ""))
                sock.settimeout(min(5.0, self.connect_timeout))
                sock.connect(p)
                req = (f"CONNECT {host}:{port} HTTP/1.1\r\n"
                       f"Host: {host}:{port}\r\n"
                       f"Proxy-Connection: Keep-Alive\r\n\r\n")
                sock.sendall(req.encode("ascii"))
                resp = b""
                while b"\r\n\r\n" not in resp and len(resp) < 8192:
                    chunk = sock.recv(1024)
                    if not chunk:
                        raise OSError("代理提前关闭")
                    resp += chunk
                first = resp.split(b"\r\n", 1)[0]
                if b" 200 " not in first:
                    raise OSError(f"代理拒绝: {first.decode('ascii', 'replace')}")
                sock.settimeout(None)
            else:
                sock.setblocking(False)
                rc = sock.connect_ex(target)
                if rc not in (0, errno.EINPROGRESS, errno.EALREADY,
                              errno.EWOULDBLOCK, 10035):  # 10035=WSAEWOULDBLOCK
                    raise OSError(f"connect_ex -> {rc}")
                if blocking and rc != 0:
                    deadline = time.monotonic() + self.connect_timeout
                    while time.monotonic() < deadline:
                        _, w, _ = select.select([], [sock], [], 0.1)
                        if w:
                            break
                    err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if err:
                        raise OSError(f"SO_ERROR={err}")
                    if not w and err == 0:
                        raise OSError("connect 超时")
            sock.setblocking(False)
            if old is not None and old is not sock:
                try:
                    old.close()
                except OSError:
                    pass
            slot.sock = sock
            slot.state = DSM_SOC_CONNECTED
            slot.read_stat = DSM_SOC_READABLE
            slot.write_stat = DSM_SOC_WRITEABLE
            slot.real_connected = True
            slot.peer = (host, port)
            return MR_SUCCESS if blocking else (MR_SUCCESS if rc == 0 else MR_WAITING)
        except OSError as exc:
            self.log(f"[net] 连接 {host}:{port} 失败: {exc}")
            try:
                sock.close()
            except (OSError, UnboundLocalError):
                pass
            slot.state = DSM_SOC_ERR
            slot.read_stat = DSM_SOC_NOREAD
            slot.write_stat = DSM_SOC_NOWRITE
            return MR_FAILED

    def connect(self, s: int, ip: int, port: int, conn_type: int) -> int:
        """``mr_connect(int32 s, int32 ip, uint16 port, int32 type)``。"""
        slot = self._slot(s)
        if slot is None or slot.sock is None:
            return MR_FAILED
        self.stats["connect"] += 1
        port = int(port) & 0xFFFF
        blocking = conn_type == MR_SOCKET_BLOCK
        ip_u = ip & 0xFFFFFFFF

        ip_text = u32_to_ip(ip_u)
        # 1) source 是点分 IP 的显式映射优先 —— 例如把 cmwap 网关直接指到
        #    复刻服务器（skyengine-v2 的 "10.0.0.172->159.75.119.124:13230"）。
        direct = self.find_mapping(ip_text)
        if direct:
            target_host = direct.address
            target_port = direct.port if direct.port is not None else port
            slot.is_proxy = False
            slot.real_connected = False
            slot.peer = (target_host, target_port)
            self.log(f"[net] connect({s}) {ip_text}:{port} -> dns-map "
                     f"{target_host}:{target_port}")
            rc = self._dial(slot, target_host, target_port, blocking)
            if rc == MR_WAITING:
                slot.state = DSM_SOC_CONNECTING
                slot.connect_at = time.monotonic()
            return rc

        # 2) cmwap 网关：交给进程内 WAP 代理。先给假的已连接状态，
        #    第一次 send 时从请求行 / Host 头找真主机（等价于 10.0.0.172 上
        #    那个已经关停的移动网关）。
        if ip_u == CMWAP_PROXY_IP and self.wap_proxy:
            slot.state = DSM_SOC_CONNECTED
            slot.read_stat = DSM_SOC_READABLE
            slot.write_stat = DSM_SOC_WRITEABLE
            slot.is_proxy = True
            slot.real_connected = False
            slot.host = ""
            slot.peer = ("10.0.0.172", port)
            self.log(f"[net] connect({s}) -> 内置 WAP 代理，等待首个请求")
            return MR_SUCCESS

        # 3) getHostByName 拿到的已经是映射后的 IP；若该映射还指定了端口，
        #    这里补上（Rust 引擎 route_mr_endpoint 的第三条规则）。
        for m in self.dns_map:
            if m.address == ip_text and m.port is not None:
                port = m.port
                break

        host = ip_text
        slot.peer = (host, port)
        self.log(f"[net] connect({s}, {host}:{port}, "
                 f"{'block' if blocking else 'nonblock'})")
        rc = self._dial(slot, host, port, blocking)
        if rc == MR_WAITING:
            slot.state = DSM_SOC_CONNECTING
            slot.connect_at = time.monotonic()
        return rc

    def get_socket_state(self, s: int) -> int:
        """``mr_getSocketState(int32 s)``: SUCCESS / WAITING / FAILED。"""
        slot = self._slot(s)
        if slot is None or slot.sock is None:
            return MR_FAILED
        if slot.state == DSM_SOC_CONNECTED:
            return MR_SUCCESS
        if slot.state != DSM_SOC_CONNECTING:
            return MR_FAILED
        try:
            _, w, _ = select.select([], [slot.sock], [], 0)
            if not w:
                if time.monotonic() - slot.connect_at > self.connect_timeout:
                    slot.state = DSM_SOC_ERR
                    return MR_FAILED
                return MR_WAITING
            err = slot.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err:
                slot.state = DSM_SOC_ERR
                return MR_FAILED
            slot.state = DSM_SOC_CONNECTED
            slot.read_stat = DSM_SOC_READABLE
            slot.write_stat = DSM_SOC_WRITEABLE
            return MR_SUCCESS
        except OSError:
            slot.state = DSM_SOC_ERR
            return MR_FAILED

    def close_socket(self, s: int) -> int:
        slot = self._slot(s)
        if slot is None:
            return MR_FAILED
        if slot.sock is not None:
            try:
                slot.sock.close()
            except OSError:
                pass
        slot.reset()
        return MR_SUCCESS

    # ------------------------------------------------------------ 收发
    def recv(self, s: int, buf: int, length: int) -> int:
        slot = self._slot(s)
        if slot is None or slot.sock is None or slot.state == DSM_SOC_ERR:
            return MR_FAILED
        if slot.read_stat != DSM_SOC_READABLE:
            return MR_FAILED
        n = max(0, min(int(length), 1 << 20))
        if n == 0:
            return 0
        # CONNECT 隧道的 "200 Connection Established" 是代理自己生成的，
        # 要排在真实上游数据之前交给 MRP。
        if slot.pending_recv:
            take = min(n, len(slot.pending_recv))
            chunk = bytes(slot.pending_recv[:take])
            del slot.pending_recv[:take]
            return take if self._write(buf, chunk) else MR_FAILED
        try:
            data = slot.sock.recv(n)
        except (BlockingIOError, InterruptedError):
            return 0
        except OSError as exc:
            self.log(f"[net] recv({s}) 失败: {exc}")
            slot.state = DSM_SOC_ERR
            return MR_FAILED
        if not data:                       # 对端关闭
            return 0
        if not self._write(buf, data):
            return MR_FAILED
        self.stats["recv"] += 1
        self.stats["recv_bytes"] += len(data)
        return len(data)

    def _ensure_proxy_link(self, slot: SocketSlot, payload: bytes) -> bool:
        """内置 WAP 代理：解析首个请求，按 dns-map 找真实服务器并建链。"""
        parsed = parse_proxy_request(payload)
        if not parsed:
            self.log("[net] WAP 代理无法解析首个请求，保持假连接")
            return slot.real_connected
        host, port, mode, outbound = parsed
        target_host, target_port = self.resolve_target(host, port)
        slot.host = f"{host}:{port}"      # 原始 authority，供诊断与旧断言
        slot.first_rewrite = outbound
        self.log(f"[net] WAP {mode} {host}:{port} -> "
                 f"{target_host}:{target_port}")
        rc = self._dial(slot, target_host, target_port, blocking=True)
        if rc != MR_SUCCESS:
            slot.first_rewrite = None
            return False
        if mode == "connect":
            slot.tunnel = True
            slot.pending_recv.extend(
                b"HTTP/1.1 200 Connection Established\r\n\r\n")
        return True

    def _send_all(self, slot: SocketSlot, data: bytes) -> bool:
        """把改写过的首包完整送出（MRP 看到的 send 长度仍是原请求长度）。"""
        view = memoryview(data)
        sent = 0
        deadline = time.monotonic() + 2.0
        while sent < len(view):
            try:
                n = slot.sock.send(view[sent:])
                if n <= 0:
                    return False
                sent += n
            except (BlockingIOError, InterruptedError):
                if time.monotonic() > deadline:
                    return False
                select.select([], [slot.sock], [], 0.02)
            except OSError as exc:
                self.log(f"[net] WAP 转发失败: {exc}")
                slot.state = DSM_SOC_ERR
                return False
        self.stats["send"] += 1
        self.stats["send_bytes"] += sent
        return True

    def send(self, s: int, buf: int, length: int) -> int:
        slot = self._slot(s)
        if slot is None or slot.sock is None or slot.state == DSM_SOC_ERR:
            return MR_FAILED
        data = self._read(buf, length)
        if not data:
            return 0
        if slot.is_proxy and not slot.real_connected:
            if not self._ensure_proxy_link(slot, data):
                return MR_FAILED
        if slot.first_rewrite is not None:
            outbound = slot.first_rewrite
            slot.first_rewrite = None
            if not outbound:            # CONNECT 头由代理自己消化，首包不发
                return len(data)
            if not self._send_all(slot, outbound):
                return MR_FAILED
            return len(data)
        if slot.write_stat != DSM_SOC_WRITEABLE:
            return MR_FAILED
        try:
            n = slot.sock.send(data)
        except (BlockingIOError, InterruptedError):
            return 0
        except OSError as exc:
            self.log(f"[net] send({s}) 失败: {exc}")
            slot.state = DSM_SOC_ERR
            return MR_FAILED
        self.stats["send"] += 1
        self.stats["send_bytes"] += max(0, n)
        return n

    def recvfrom(self, s: int, buf: int, length: int,
                 ip_ptr: int, port_ptr: int) -> int:
        slot = self._slot(s)
        if slot is None or slot.sock is None or slot.state == DSM_SOC_ERR:
            return MR_FAILED
        n = max(0, min(int(length), 1 << 20))
        if n == 0:
            return 0
        try:
            data, (peer_ip, peer_port) = slot.sock.recvfrom(n)
        except (BlockingIOError, InterruptedError):
            return 0
        except OSError:
            slot.state = DSM_SOC_ERR
            return MR_FAILED
        if not self._write(buf, data):
            return MR_FAILED
        mem = self._mem()
        if ip_ptr and mem.valid(ip_ptr, 4):
            mem.set_u32(ip_ptr, ip_to_u32(peer_ip))
        if port_ptr and mem.valid(port_ptr, 2):
            mem.set_u16(port_ptr, peer_port)
        self.stats["recv"] += 1
        self.stats["recv_bytes"] += len(data)
        return len(data)

    def sendto(self, s: int, buf: int, length: int, ip: int, port: int) -> int:
        slot = self._slot(s)
        if slot is None or slot.sock is None or slot.state == DSM_SOC_ERR:
            return MR_FAILED
        data = self._read(buf, length)
        if not data:
            return 0
        try:
            n = slot.sock.sendto(data, (u32_to_ip(ip), int(port) & 0xFFFF))
        except (BlockingIOError, InterruptedError):
            return 0
        except OSError as exc:
            self.log(f"[net] sendto({s}) 失败: {exc}")
            slot.state = DSM_SOC_ERR
            return MR_FAILED
        self.stats["send"] += 1
        self.stats["send_bytes"] += max(0, n)
        return n

    # ------------------------------------------------------------ 诊断
    def report(self) -> str:
        live = [i for i, s in enumerate(self.slots) if s.state != DSM_SOC_CLOSE]
        return (f"网络: {'开' if self.initialized else '未初始化'} "
                f"mode={self.mode or '-'} 活跃socket={live} "
                f"proxy={self.http_proxy or '-'} "
                f"dns-map={len(self.dns_map)} wap={'on' if self.wap_proxy else 'off'} | " +
                " ".join(f"{k}={v}" for k, v in self.stats.items()))
