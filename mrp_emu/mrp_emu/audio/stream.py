"""流式 PCM 播放 —— 分段喂入、无缝拼接。

这是第二条播放通路，和 mr_playSound 一次给全量数据不同：

MRP 侧（语音、在线流媒体、软波表合成器）会**持续**把小块 PCM 推过来，
单块常常只有几十毫秒（``MR_SOUND_PCM //8K`` 指 8kHz 16bit）。如果每块
直接 play，会变成一顿一顿的爆音；正确做法是攒块 + 排队 + 每帧补齐。

pygame 的 Channel 只有一个 queue 槽位，所以要靠 tick() 不断续投。
积压太多时丢旧块 —— 流媒体场景下「实时」比「完整」重要。
"""

from __future__ import annotations

import numpy as np

from .wav import resample

_BYTES_PER_SAMPLE = 2          # 只处理 16bit


class PcmStream:
    """一路流式 PCM 播放器（对应 mr_playSound(MR_SOUND_PCM, ...) 的连续调用）。"""

    def __init__(self, engine, rate: int = 8000, channels: int = 1,
                 chunk_ms: int = 120, max_lag_ms: int = 1200) -> None:
        self.engine = engine
        self.rate = max(1000, int(rate))
        self.channels = max(1, int(channels))
        self.chunk_ms = max(20, int(chunk_ms))
        lag_seconds = max(0.2, max_lag_ms / 1000.0)
        self.max_lag_bytes = int(self.rate * lag_seconds) * _BYTES_PER_SAMPLE * self.channels

        self._buf = bytearray()
        self._ready: list = []          # 待投递的 pygame Sound
        self.ch = None
        self.fed_bytes = 0
        self.played_chunks = 0
        self.dropped_bytes = 0
        self.active = False

    # ------------------------------------------------------------ 生命周期
    def _ensure_channel(self):
        if self.ch is None and self.engine.ok:
            import pygame
            self.ch = pygame.mixer.Channel(self.engine.stream_channel)
        return self.ch

    def start(self) -> None:
        """开始一路新流：清掉旧数据。"""
        self._buf.clear()
        self._ready.clear()
        self.fed_bytes = 0
        self.played_chunks = 0
        self.active = True
        ch = self._ensure_channel()
        if ch is not None:
            ch.stop()
        if self.engine.log:
            self.engine.log(f"[audio] PCM 流开始 ({self.rate}Hz/{self.channels}ch)")

    def stop(self) -> None:
        self.active = False
        self._buf.clear()
        self._ready.clear()
        if self.ch is not None:
            self.ch.stop()
        if self.engine.log:
            self.engine.log("[audio] PCM 流停止")

    # ------------------------------------------------------------ 喂数据
    def feed(self, pcm: bytes) -> None:
        """追加一段 PCM。MRP 每次调 mr_playSound(MR_SOUND_PCM) 就走这里。"""
        if not pcm:
            return
        if not self.active:
            self.start()
        self.fed_bytes += len(pcm)
        self._buf.extend(pcm)

        # 积压过多：丢掉最老的，保住实时性
        if len(self._buf) > self.max_lag_bytes:
            frame_bytes = _BYTES_PER_SAMPLE * self.channels
            drop = len(self._buf) - self.max_lag_bytes
            drop -= drop % frame_bytes
            if drop > 0:
                del self._buf[:drop]
                self.dropped_bytes += drop

        self._drain()

    def _drain(self) -> None:
        """把缓冲里够一块的数据切成 Sound 扔进待播队列。"""
        if not self.engine.ok:
            return
        frame_bytes = _BYTES_PER_SAMPLE * self.channels
        chunk_bytes = max(frame_bytes * 64,
                          int(self.rate * self.chunk_ms / 1000.0) * frame_bytes)
        while len(self._buf) >= chunk_bytes and len(self._ready) < 6:
            block = bytes(self._buf[:chunk_bytes])
            del self._buf[:chunk_bytes]
            sound = self._make_sound(block)
            if sound is not None:
                self._ready.append(sound)
        self._fill()

    def _make_sound(self, block: bytes):
        import pygame
        arr = np.frombuffer(block, dtype="<i2").astype(np.float32) / 32768.0
        if self.channels > 1:
            n = (arr.size // self.channels) * self.channels
            arr = arr[:n].reshape(-1, self.channels).mean(axis=1)
        out_rate = self.engine.sample_rate
        if self.rate != out_rate:
            arr = resample(arr, self.rate, out_rate)
        # 块首尾各 1ms 微渐变，消除块边界可能出现的咔哒声
        fade = min(arr.size // 2, max(1, int(out_rate * 0.001)))
        if fade > 1:
            ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
            arr[:fade] *= ramp
            arr[-fade:] *= ramp[::-1]
        data = np.clip(arr, -1.0, 1.0)
        pcm16 = (data * 32767.0).astype("<i2")
        if self.engine.channels > 1:
            pcm16 = np.repeat(pcm16, self.engine.channels)
        try:
            return pygame.mixer.Sound(buffer=pcm16.tobytes())
        except Exception as exc:                     # pragma: no cover
            if self.engine.log:
                self.engine.log(f"[audio] 流块创建失败：{exc}")
            return None

    # ------------------------------------------------------------ 续投
    def _fill(self) -> None:
        ch = self._ensure_channel()
        if ch is None or not self._ready:
            return
        if not ch.get_busy():
            ch.play(self._ready.pop(0))
            self.played_chunks += 1
        elif ch.get_queue() is None:
            ch.queue(self._ready.pop(0))
            self.played_chunks += 1

    def tick(self) -> None:
        """每帧调一次：queue 槽空出来就补下一块，保持连续。"""
        if not self.active:
            return
        if self._buf:
            self._drain()
        else:
            self._fill()
            # 缓冲空了但还有待播：让队列继续消耗
            if not self._ready and self.ch is not None and not self.ch.get_busy():
                self.active = False               # 一轮流播完，等下段数据再开

    # ------------------------------------------------------------ 诊断
    def stats(self) -> str:
        sec = self.fed_bytes / float(_BYTES_PER_SAMPLE * self.channels * self.rate)
        return (f"PCM流 {self.rate}Hz/{self.channels}ch 共 {sec:.2f}s | "
                f"已播 {self.played_chunks} 块 | 丢弃 {self.dropped_bytes}B")
