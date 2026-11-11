"""为 RX 管理器回归测试构造**固定的隔离运行环境**。

为什么不能直接拿 ``runtime/`` 跑：RX 管理器（以及浏览器类应用）运行时会
在 ``mythroad/`` 下自建 ``brw/``、``cookie/``、``app240320/``、``*.sid``
等缓存目录。这些目录是「上一次跑出来的结果」，会让下一次的目录枚举和
90 步固定按键序列走进完全不同的分支 —— 2026-11-10 实测因此出现过
``PC=0x2E26AE`` 读野指针 ``0xF82D4AE8`` 的崩溃（属于应用自身对目录项的
容错问题，不是图形/网络回归）。用 HEAD 原版代码复跑同样失败，确认与
模拟器改动无关。

所以这里只复制**固定的文件集**：``cfunction.ext`` + ``mythroad/*.mrp``，
不带任何应用自建缓存目录，保证每次断言的输入完全一致。

字库（``mythroad/system/gb16.uc2``）也一并带上：DSM 层的应用启动第一件事
就是 open 它来画中文，缺了会打 ``font load fail``，界面上的汉字全空
（见 docs/21）。优先带原厂字库，没有就现场生成一份。
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable

RX_MRP = "R_Xplore_MTK_all（RX管理器）.mrp"


def _copy_font(src: Path, td: Path) -> None:
    """把系统点阵字库带进隔离环境。"""
    system = td / "mythroad" / "system"
    system.mkdir(parents=True, exist_ok=True)
    try:
        from mrp_emu.fontgen import ensure_uc2
        ensure_uc2(system / "gb16.uc2", log=lambda *a: None,
                   factory_dirs=[src / "mythroad" / "fonts",
                                 src / "mythroad" / "system"])
    except Exception:  # pragma: no cover - 字库不可用不该让测试崩
        pass


def make_rx_env(runtime: str | Path) -> tuple[Path | None, Callable[[], None]]:
    """返回 ``(workdir, cleanup)``；运行环境不完整时返回 ``(None, noop)``。"""
    src = Path(runtime)
    ext = src / "cfunction.ext"
    rx = src / "mythroad" / RX_MRP
    if not ext.is_file() or not rx.is_file():
        return None, lambda: None

    td = Path(tempfile.mkdtemp(prefix="pymrp-rx-env-"))
    (td / "mythroad").mkdir()
    shutil.copy2(ext, td / "cfunction.ext")
    # 只收 .mrp 文件：目录、.sid、应用缓存一律不带
    for p in sorted((src / "mythroad").glob("*.mrp")):
        shutil.copy2(p, td / "mythroad" / p.name)
    _copy_font(src, td)

    def cleanup() -> None:
        shutil.rmtree(td, ignore_errors=True)

    return td, cleanup
