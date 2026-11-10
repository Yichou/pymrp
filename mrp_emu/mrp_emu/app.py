"""宿主应用上下文：把内存、文件系统、图形、定时器粘在一起。"""

from __future__ import annotations

import time
from pathlib import Path

from .audio import AudioEngine
from .fs import VirtualFs
from .gfx import Gfx
from .net import NetEngine


class App:
    def __init__(self, vm, workdir: str | Path, log=print,
                 audio: bool = True, sample_rate: int = 44100,
                 pcm_rate: int = 8000, audio_engine=None,
                 http_proxy: str = "", net_enabled: bool = True,
                 dns_map: str | None = None, wap_proxy: bool = True) -> None:
        self.vm = vm
        self.log = log
        self.fs = VirtualFs(workdir)
        self.gfx = Gfx(vm.mem)
        # 切换应用会重建 VM，但整机只有一个喇叭：音频引擎在多次会话间复用，
        # 避免反复 pygame.mixer.init() 和缓存泄漏。
        self.audio = audio_engine or AudioEngine(
            sample_rate=sample_rate, enabled=audio, log=log, pcm_rate=pcm_rate)
        # 网络状态机跟 VM 绑定（回调要 call_arm），所以每次重建 VM 也重建一份。
        self.net = NetEngine(vm, log=log, enabled=net_enabled,
                             http_proxy=http_proxy, dns_map=dns_map,
                             wap_proxy=wap_proxy)

        self.t0 = time.monotonic()
        self.timer_interval = 0
        self.next_timer_at = 0.0
        self.timer_hits = 0

        self._scratch: dict[str, int] = {}
        self._edit_texts: dict[int, str] = {}
        self.mrp_name = ""
        self.status = "就绪"

    # ------------------------------------------------------------ 时间
    def uptime_ms(self) -> int:
        return int((time.monotonic() - self.t0) * 1000)

    def shutdown_session(self, reason: str = "") -> dict:
        """退出 / 崩溃时的**统一收尾**：停声音、关网络、关文件句柄。

        MRP 侧的 ``mr_exit()`` 只置一个标志位，真正干活的是这里。以前
        只关了 socket，于是退到系统界面后背景音乐还在响、文件句柄一直
        占着（句柄号会被下一次会话复用，MRP 侧可能读到别的文件）。

        返回收尾统计，便于日志与回归测试断言。
        """
        info: dict = {"reason": reason, "sockets": 0, "files": 0, "audio": False}
        try:
            self.net.close_network()
            info["sockets"] = len(getattr(self.net, "slots", []) or [])
        except Exception:  # noqa: BLE001 - 收尾不能因为单项失败而中断
            pass
        try:
            info["files"] = self.fs.close_all()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.audio.stop_all()
            info["audio"] = True
        except Exception:  # noqa: BLE001
            pass
        return info

    def timer_start(self, ms: int) -> None:
        self.timer_interval = max(0, ms)
        self.next_timer_at = time.monotonic() + self.timer_interval / 1000.0

    def timer_stop(self) -> None:
        self.timer_interval = 0

    def timer_due(self) -> bool:
        if self.timer_interval <= 0:
            return False
        now = time.monotonic()
        if now < self.next_timer_at:
            return False
        self.next_timer_at = now + self.timer_interval / 1000.0
        self.timer_hits += 1
        return True

    # ------------------------------------------------------------ 临时字符串
    def scratch_str(self, text: str, slot: str = "edit", size: int = 256) -> int:
        """给 ARM 侧返回一个稳定指针（MRP 里这类返回值通常不要求释放）。"""
        addr = self._scratch.get(slot)
        if addr is None:
            addr = self.vm.mem.malloc(size)
            self._scratch[slot] = addr
        raw = text.encode("gbk", errors="replace")[: size - 1]
        self.vm.mem.write(addr, raw + b"\x00")
        return addr

    def take_edit_text(self, handle: int) -> str | None:
        return self._edit_texts.pop(handle, None)

    def feed_text(self, text: str) -> None:
        """给当前编辑框喂文本（宿主侧输入法/键盘用）。"""
        if self._edit_texts:
            last = max(self._edit_texts)
            self._edit_texts[last] += text

    # ------------------------------------------------------------ 诊断
    def report(self) -> str:
        t1 = self.vm.tables.get("mr_table")
        t2 = self.vm.tables.get("dsm")
        lines = [
            f"MRP: {self.mrp_name or '(未加载)'}",
            f"内存: {self.vm.mem.heap.report()}",
            f"帧: {self.gfx.frames} | 定时器: {self.timer_hits} 次 (间隔 {self.timer_interval}ms)",
        ]
        for t in (t1, t2):
            if t is None:
                continue
            hit = sum(t.calls.values())
            lines.append(
                f"{t.name}: {len(t.dispatch)} 槽位 | 调用 {hit} 次 | "
                f"未实现 {len({f.name for f in t.funcs if f.fn is None})} 项"
            )
        return "\n".join(lines)
