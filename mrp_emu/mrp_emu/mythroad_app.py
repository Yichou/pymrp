"""自编译 mythroad VM 的宿主应用上下文。

与老架构（`app.App`）的区别：

* 帧缓冲**不是我们分配的** —— mythroad 自己分配（全局变量 ``mr_screenBuf``），
  我们只能用惰性代理绑定上去；
* 内存视图是 ``VmSpace``（0x880000 以上），与老 VM 的 0x80000 段不重叠；
* 网络回调机制不同（新 VM 没有 ``call_arm``），先不接网络。

之所以要单独的类而不是复用 ``app.App``：老 App 的 Gfx 会自己 malloc 帧缓冲，
而新架构必须绑定 mythroad 的那块。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from .fs import VirtualFs
from .gfx import Gfx


class LazyGfx:
    """帧缓冲代理：第一次真正用到时才绑定 mythroad 的 ``mr_screenBuf``。

    mythroad 在 ``_mr_intra_start`` 里分配屏幕缓冲，**早于**应用第一帧，
    所以第一次访问 gfx 时地址一定已经就绪。
    """

    def __init__(self, vm) -> None:
        self.vm = vm
        self._gfx: Gfx | None = None

    def resolve(self) -> Gfx:
        if self._gfx is None:
            fb = self.vm.screen_buf_addr()
            self._gfx = Gfx(self.vm.mem, fb_addr=fb)
        return self._gfx

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.resolve(), name)


class MythroadApp:
    """宿主侧的应用状态：文件系统、图形、定时器。"""

    def __init__(self, vm, workdir: str | Path,
                 log: Callable[[str], None] = print) -> None:
        self.vm = vm
        self.log = log
        self.fs = VirtualFs(workdir)
        self.gfx = LazyGfx(vm)
        # 网络/音频先留空：新架构的回调机制还没接上，
        # 相关接口会返回 MR_FAILED，不影响应用跑起来。
        self.audio = None
        self.net = None

        self.t0 = time.monotonic()
        self.timer_interval = 0
        self.next_timer_at = 0.0
        self.timer_hits = 0

        self.mrp_name = ""
        self.status = "就绪"

    # ------------------------------------------------------------ 时间
    def uptime_ms(self) -> int:
        return int((time.monotonic() - self.t0) * 1000)

    def timer_start(self, ms: int) -> None:
        self.timer_interval = max(0, ms)
        self.next_timer_at = time.monotonic() + self.timer_interval / 1000.0

    def timer_stop(self) -> None:
        self.timer_interval = 0
        self.next_timer_at = 0.0

    def timer_due(self) -> bool:
        return bool(self.timer_interval) and time.monotonic() >= self.next_timer_at

    def tick_timer(self) -> None:
        """定时器到点：推进到下一个周期。"""
        self.timer_hits += 1
        self.next_timer_at = time.monotonic() + self.timer_interval / 1000.0
