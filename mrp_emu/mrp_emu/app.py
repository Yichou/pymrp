"""宿主应用上下文：把内存、文件系统、图形、定时器粘在一起。"""

from __future__ import annotations

import time
from pathlib import Path

from .audio import AudioEngine
from .fs import VirtualFs
from .gfx import Gfx


class App:
    def __init__(self, vm, workdir: str | Path, log=print,
                 audio: bool = True, sample_rate: int = 44100,
                 pcm_rate: int = 8000, audio_engine=None) -> None:
        self.vm = vm
        self.log = log
        self.fs = VirtualFs(workdir)
        self.gfx = Gfx(vm.mem)
        # 切换应用会重建 VM，但整机只有一个喇叭：音频引擎在多次会话间复用，
        # 避免反复 pygame.mixer.init() 和缓存泄漏。
        self.audio = audio_engine or AudioEngine(
            sample_rate=sample_rate, enabled=audio, log=log, pcm_rate=pcm_rate)

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
