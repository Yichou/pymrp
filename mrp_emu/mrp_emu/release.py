"""把 MRP 包内的资源释放到运行目录（模拟真机行为）。

为什么需要
----------
MTK 真机上，MRP 应用把图标、WML 模板等资源**打包在 .mrp 里**，启动时
再由运行时释放到应用自己的目录，例如::

    E:\\QQ2010\\res\\icon_logo.gif
    E:\\QQ2010\\res\\mtt_start.wml

``391032_240320_atxqq.mrp``（爱Q手机QQ）就是这样：包内带
``mtt_start.wml`` / ``icon_*.gif``，运行时把它们释放到 ``QQ2010/res/``，
然后浏览器引擎按 ``file://E:\\QQ2010\\res\\...`` 读回去。

我们的模拟器只把 .mrp 当成「可执行文件」跑，没做资源释放，于是应用
打开 ``mythroad/QQ2010/res/icon_*.gif`` 全部失败，页面渲染成空白。

本模块提供 :func:`release_mrp_resources`，把包内条目按应用自己的目录
约定释放出去。释放到哪里由应用决定 —— 通用做法是：

* 资源在包内**根目录**（``mtt_start.wml``、``icon_*.gif``）——
  这些是「应用私有资源」，落到 ``<appdir>/res/``；
* ``.mr`` / ``.ext`` / ``start.mr`` 等代码条目 —— 不释放（本来就是入口）。

约定：通过 :func:`resource_release_plan` 计算「条目 -> 目标相对路径」。
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from .catalog import MrpEntry, read_mrp_entries, read_mrp_entry_data

# 视为「代码」而不释放的扩展名（运行时自己会从包里读）
CODE_EXTS = (".mr", ".ext", ".mid", ".mel", ".dat", ".bin")

# 应用私有资源的目录名（真机约定）
RES_DIR = "res"

# 真机上的绝对路径前缀，例如 "E:\QQ2010\Cache\%u.dat"
_ABS_PATH_RE = re.compile(rb"[A-Za-z]:[\\/]([A-Za-z0-9_ .\-]{1,40})[\\/]")


def detect_app_dirs(mrp_path: str | Path) -> list[str]:
    """从包内资源里反推应用自己的目录名。

    真机上的 MTK 应用普遍把自己的数据放在 ``E:\\<AppName>\\``，包里
    的 WML / 脚本里会写死这种绝对路径。我们扫一遍包内内容，统计
    ``E:\\xxx\\`` 里的 ``xxx`` 出现频次，取最常见的作为应用目录名。

    实测：

    * ``391032_240320_atxqq.mrp`` -> ``["QQ2010", "QQ2010Download"]``
    * ``dsm_gm.mrp`` -> ``["downdata"]``
    """
    mrp_path = Path(mrp_path)
    entries = read_mrp_entries(mrp_path)
    if not entries:
        return []
    counter: dict[str, int] = {}
    for e in entries:
        try:
            data = read_mrp_entry_data(mrp_path, e)
        except OSError:
            continue
        if not data:
            continue
        for m in _ABS_PATH_RE.finditer(data):
            name = m.group(1).decode("ascii", "replace").strip().rstrip("\\")
            if not name or name in (".", ".."):
                continue
            counter[name] = counter.get(name, 0) + 1
    if not counter:
        return []
    # 频次高的排前面；同频按名字排序保证稳定
    return [name for name, _ in sorted(counter.items(),
                                       key=lambda kv: (-kv[1], kv[0]))]


def resource_release_plan(entries: list[MrpEntry],
                          app_dir: str = "QQ2010",
                          res_dir: str = RES_DIR,
                          root: str = "mythroad") -> dict[str, str]:
    """算出「包内条目名 -> 运行目录下的相对路径」。

    * 图片 / WML / 文本类资源 -> ``<root>/<app_dir>/<res_dir>/<名字>``
    * 其余（数据库、配置）  -> ``<root>/<app_dir>/<名字>``
    * 代码类（``.mr``/``.ext``…）-> 不释放

    ``root`` 默认为 ``mythroad``：MRP 运行时把应用数据放在工作目录下的
    ``mythroad/`` 里（``mr_platEx(1204)`` 的 ``SetDsmWorkPath()`` 就是
    设成 ``mythroad/``），应用 open 时的相对路径也以它开头。
    """
    plan: dict[str, str] = {}
    prefix = f"{root.strip('/')}/" if root else ""
    for e in entries:
        name = e.name
        if not name or "/" in name or "\\" in name:
            continue
        low = name.lower()
        if low.endswith(CODE_EXTS):
            continue
        if low.endswith((".gif", ".png", ".jpg", ".jpeg", ".bmp", ".wml",
                         ".xml", ".html", ".htm", ".txt", ".css", ".js",
                         ".wav", ".mid", ".mp3")):
            plan[name] = f"{prefix}{app_dir}/{res_dir}/{name}"
        elif low.endswith((".db", ".dat", ".conf", ".cfg", ".cof", ".sav")):
            plan[name] = f"{prefix}{app_dir}/{name}"
    return plan


def release_mrp_resources(mrp_path: str | Path,
                           workdir: str | Path,
                           app_dir: str | None = None,
                           res_dir: str = RES_DIR,
                           root: str = "mythroad",
                           force: bool = False,
                           log=print) -> list[Path]:
    """把 MRP 内的资源释放到 ``<workdir>/<root>/`` 下，返回写出的文件列表。

    ``app_dir`` 为空时用 :func:`detect_app_dirs` 自动推断（取最常见的
    应用目录名）。

    已经存在且大小一致的文件默认跳过（``force=True`` 可强制重写）——
    释放是幂等的，不必每次启动都重写一遍。
    """
    mrp_path = Path(mrp_path)
    workdir = Path(workdir)
    entries = read_mrp_entries(mrp_path)
    if not entries:
        return []
    if not app_dir:
        dirs = detect_app_dirs(mrp_path)
        app_dir = dirs[0] if dirs else ""
    if not app_dir:
        return []
    plan = resource_release_plan(entries, app_dir, res_dir, root)
    written: list[Path] = []
    for name, rel in plan.items():
        entry = next((e for e in entries if e.name == name), None)
        if entry is None:
            continue
        data = read_mrp_entry_data(mrp_path, entry)
        if not data:
            continue
        dst = workdir / rel
        try:
            if dst.exists() and not force and dst.stat().st_size == len(data):
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            written.append(dst)
        except OSError as exc:
            if log:
                log(f"[release] 释放 {name} 失败: {exc}")
    if written and log:
        log(f"[release] 已从 {mrp_path.name} 释放 {len(written)} 个资源"
            f"到 {root}/{app_dir}/")
    return written


def release_into(mrp_path: str | Path, workdir: str | Path,
                 log=print) -> list[Path]:
    """便捷入口：按应用目录名自动释放。

    应用目录名取 MRP 的 ``appid``/标题都不可靠，这里统一用「包所在目录
    下的约定名」：调用方一般知道自己在跑哪个应用。
    """
    return release_mrp_resources(mrp_path, workdir, log=log)
