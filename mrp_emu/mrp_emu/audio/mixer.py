"""音频门面：把 MRP 的 mr_playSound / mr_stopSound 接到 pygame.mixer。

MRP 侧只有两个入口（见 mrporting.h）：

    int32 mr_playSound(int type, const void *data, uint32 dataLen, int32 loop);
    int32 mr_stopSound(int type);

``type`` 是 MR_SOUND_TYPE：MIDI / WAV / MP3 / PCM / M4A / AMR / AMR_WB。
``data`` 是**模拟内存里的指针** —— 不是文件名。应用总是先把音频读进内存
（mr_open + mr_read，或者直接嵌在代码段），再把这个指针递过来。所以我们
必须先 mem.read 出来，才能谈解码。

两条通路在这里合流：
  · 一次性数据（MIDI/WAV）→ 解码 → 缓存 → Channel.play
  · MR_SOUND_PCM → 分段流 → stream.PcmStream 攒块排队
"""

from __future__ import annotations

import hashlib
import io
import time
from collections import OrderedDict

from ..consts import (
    MR_FAILED,
    MR_SOUND_AMR,
    MR_SOUND_AMR_WB,
    MR_SOUND_M4A,
    MR_SOUND_MIDI,
    MR_SOUND_MP3,
    MR_SOUND_PCM,
    MR_SOUND_WAV,
    MR_SUCCESS,
    SOUND_TYPE_NAMES,
)
from . import midi as midi_mod
from . import synth
from . import wav as wav_mod
from .media import MediaRack
from .stream import PcmStream

_CACHE_LIMIT = 64
_EFFECT_CHANNELS = 8          # 0-7 给 mr_playSound，8 给 PCM 流，9 给流媒体播放器
_PCM_CHANNEL = _EFFECT_CHANNELS
_MEDIA_CHANNEL = _EFFECT_CHANNELS + 1
_BG_CHANNEL_BASE = _EFFECT_CHANNELS + 2


class AudioEngine:
    """一台功能机的音频子系统（单喇叭、单声道、有限复音）。"""

    def __init__(self, sample_rate: int = 44100, enabled: bool = True,
                 log=print, pcm_rate: int = 8000, pcm_channels: int = 1) -> None:
        self.sample_rate = int(sample_rate)
        self.channels = 2
        self.ok = False
        self.enabled = enabled
        self.log = log
        self.volume = 0.8

        self.pcm_rate = int(pcm_rate)
        self.pcm_channels = max(1, int(pcm_channels))

        # mr_plat(102/103) 的 PCM 环形缓冲状态
        self._ring_last: int | None = None
        self._ring_base = 0
        self._ring_t0 = 0.0
        self.ring_bytes = 0

        self.stream: PcmStream | None = None
        self.stream_channel = _PCM_CHANNEL
        self._media_ch = None
        self.media = MediaRack(self)

        self._channels: dict[int, object] = {}
        self._cache: "OrderedDict[bytes, object]" = OrderedDict()
        self._hold: dict[int, object] = {}      # 正在播的 Sound 保活
        self._music_type: int | None = None

        # 统计（--stats 和自检都会看）
        self.calls = 0
        self.plays = 0
        self.failures = 0
        self.render_ms = 0.0
        self.last_desc = ""
        self.last_pcm = b""                     # 最近一次渲染的 PCM，供自检断言

        if enabled:
            self._init()

    # ------------------------------------------------------------ 初始化
    def _init(self) -> None:
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=self.sample_rate, size=-16,
                    channels=self.channels, buffer=1024,
                )
            got = pygame.mixer.get_init()
            if got:
                self.sample_rate, _, self.channels = int(got[0]), got[1], int(got[2])
            pygame.mixer.set_num_channels(max(16, _EFFECT_CHANNELS + 8))
            self.ok = True
            if self.log:
                self.log(f"[audio] mixer 就绪 {self.sample_rate}Hz/{self.channels}ch")
        except Exception as exc:
            self.ok = False
            if self.log:
                self.log(f"[audio] mixer 初始化失败，静音运行：{exc}")

    def _channel(self, stype: int):
        import pygame
        ch = self._channels.get(stype)
        if ch is None:
            # 每种声音类型固定一个通道：MRP 的 stopSound(type) 才有明确对象
            idx = min(_EFFECT_CHANNELS - 1, max(0, stype))
            ch = pygame.mixer.Channel(idx)
            ch.set_volume(self.volume)
            self._channels[stype] = ch
        return ch

    def media_channel_obj(self):
        """流媒体播放器专用通道（mr_platEx 204x）。"""
        import pygame
        if self._media_ch is None:
            self._media_ch = pygame.mixer.Channel(_MEDIA_CHANNEL)
            self._media_ch.set_volume(self.volume)
        return self._media_ch

    def bg_channel_index(self, handle: int) -> int:
        """多通道背景音（mr_platEx 222x-225x）：10..15 轮转复用。"""
        return _BG_CHANNEL_BASE + (max(1, handle) % 6)

    # ------------------------------------------------------------ 播放
    def play(self, stype: int, data: bytes, loop: bool) -> int:
        """对应 mr_playSound。data 是从模拟内存里读出来的原始字节。"""
        self.calls += 1
        name = SOUND_TYPE_NAMES.get(stype, f"type{stype}")

        # 枚举有历史包袱：老版 mrporting.h 是 5 值（AMR=3, PCM=4），
        # vmrp 是 7 值（PCM=3, M4A=4）。两边在 3/4 上打架，用数据头判定：
        # AMR 文件一定以 "#!AMR" 开头（AMR-WB 是 "#!AMR-WB"），
        # 其余按 8K 裸 PCM 处理。
        if stype in (MR_SOUND_PCM, MR_SOUND_M4A):
            if data[:5] == b"#!AMR":
                self.failures += 1
                if self.log:
                    self.log(f"[audio] {name} 是 AMR 数据，编解码不在模拟范围内")
                return MR_FAILED
            return self.feed_pcm(data)

        if not data:
            self.failures += 1
            if self.log:
                self.log(f"[audio] {name} 数据为空，忽略")
            return MR_FAILED

        if not self.ok:
            # 没有音频设备也要当成成功：老应用会因为失败而反复重试刷屏
            self.last_desc = f"{name} {len(data)}B（静音）"
            return MR_SUCCESS

        try:
            if stype == MR_SOUND_MIDI:
                sound, desc = self._load_midi(data)
            elif stype == MR_SOUND_WAV:
                sound, desc = self._load_wav(data)
            elif stype == MR_SOUND_MP3:
                return self._play_music(stype, data, loop, name)
            elif stype in (MR_SOUND_AMR, MR_SOUND_AMR_WB):
                self.failures += 1
                if self.log:
                    self.log(f"[audio] {name} 暂不支持（编解码不在模拟范围内）")
                return MR_FAILED
            else:
                # 未知类型：按 MIDI 试一下，不行再按 WAV
                try:
                    sound, desc = self._load_midi(data)
                except Exception:
                    sound, desc = self._load_wav(data)
        except Exception as exc:
            self.failures += 1
            if self.log:
                self.log(f"[audio] {name} 解析失败：{type(exc).__name__}: {exc}")
            return MR_FAILED

        if sound is None:
            self.failures += 1
            return MR_FAILED

        ch = self._channel(stype)
        ch.play(sound, loops=-1 if loop else 0)
        self._hold[stype] = sound
        self.plays += 1
        self.last_desc = f"{desc}{' 循环' if loop else ''}"
        if self.log:
            self.log(f"[audio] 播放 {self.last_desc}")
        return MR_SUCCESS

    def stop(self, stype: int) -> None:
        """对应 mr_stopSound。"""
        self.calls += 1
        if stype in (MR_SOUND_PCM, MR_SOUND_M4A):
            if self.stream is not None:
                self.stream.stop()
            return
        ch = self._channels.get(stype)
        if ch is not None:
            ch.stop()
        self._hold.pop(stype, None)
        if stype in (MR_SOUND_MP3, MR_SOUND_M4A) and self.ok:
            try:
                import pygame
                pygame.mixer.music.stop()
            except Exception:
                pass
        if self.log:
            self.log(f"[audio] 停止 {SOUND_TYPE_NAMES.get(stype, stype)}")

    # ------------------------------------------------------------ MIDI
    def _load_midi(self, data: bytes):
        key = b"M" + hashlib.md5(data).digest()
        hit = self._cache_get(key)
        if hit is not None:
            return hit, self.last_desc or "MIDI（缓存）"

        t0 = time.perf_counter()
        song = midi_mod.load(data)
        buf = synth.render(song, self.sample_rate)
        pcm = synth.to_stereo16(buf, self.channels)
        self.render_ms = (time.perf_counter() - t0) * 1000.0
        self.last_pcm = pcm

        import pygame
        sound = pygame.mixer.Sound(buffer=pcm)
        sound.set_volume(self.volume)
        desc = f"{song.summary()} 合成 {self.render_ms:.0f}ms"
        self.last_desc = desc
        self._cache_put(key, sound)
        return sound, desc

    # ------------------------------------------------------------ WAV
    def _load_wav(self, data: bytes):
        key = b"W" + hashlib.md5(data).digest()
        hit = self._cache_get(key)
        if hit is not None:
            return hit, self.last_desc or "WAV（缓存）"

        w = wav_mod.parse(data)
        samples = w.samples
        if w.rate != self.sample_rate:
            samples = wav_mod.resample(samples, w.rate, self.sample_rate)
        pcm = synth.to_stereo16(samples, self.channels)
        self.last_pcm = pcm

        import pygame
        sound = pygame.mixer.Sound(buffer=pcm)
        sound.set_volume(self.volume)
        desc = w.summary()
        self.last_desc = desc
        self._cache_put(key, sound)
        return sound, desc

    # ------------------------------------------------------------ MP3
    def _play_music(self, stype: int, data: bytes, loop: bool, name: str) -> int:
        """MP3/M4A 走 mixer.music：Sound 只吃 WAV 类，音乐流走另一条路。"""
        import pygame

        key = bytes([stype]) + hashlib.md5(data).digest()
        if key not in self._cache:
            try:
                pygame.mixer.music.load(io.BytesIO(data))
            except Exception as exc:
                self.failures += 1
                if self.log:
                    self.log(f"[audio] {name} 解码失败：{exc}")
                return MR_FAILED
            self._cache_put(key, True)
        try:
            pygame.mixer.music.play(-1 if loop else 0)
        except Exception:
            pass
        self._music_type = stype
        self.plays += 1
        self.last_desc = f"{name} {len(data)}B{' 循环' if loop else ''}"
        if self.log:
            self.log(f"[audio] 播放 {self.last_desc}")
        return MR_SUCCESS

    # ------------------------------------------------------------ PCM 流
    def feed_pcm(self, data: bytes) -> int:
        """MR_SOUND_PCM：分段喂入的实时流。"""
        if self.stream is None:
            self.stream = PcmStream(self, rate=self.pcm_rate,
                                    channels=self.pcm_channels)
        if not data:
            return MR_SUCCESS
        if not self.ok:
            self.last_desc = f"PCM {len(data)}B（静音）"
            return MR_SUCCESS
        self.stream.feed(data)
        self.plays += 1
        return MR_SUCCESS

    def tick(self) -> None:
        """每帧调一次：续投流式 PCM、推进流媒体播放器状态。"""
        if self.stream is not None:
            self.stream.tick()
        self.media.tick()

    def shutdown(self) -> None:
        if self.stream is not None:
            self.stream.stop()
        for player in self.media.players.values():
            player.release()
        if self.ok:
            try:
                import pygame
                pygame.mixer.stop()
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._cache.clear()
        self._hold.clear()

    # ------------------------------------------------------------ 缓存
    def _cache_get(self, key: bytes):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _cache_put(self, key: bytes, value) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > _CACHE_LIMIT:
            self._cache.popitem(last=False)

    # ------------------------------------------------------------ PCM 环形缓冲
    def ring_notify_write(self, addr: int, mem) -> None:
        """mr_plat(102)：告知驱动 PCM 已写到哪个绝对地址。

        这是最底层的流式播放：应用自己往一块内存里塞 PCM，每写一段就报一次
        地址；驱动按实时速率推进播放点，应用用 103 查回来算还能写多少。
        我们这里做两件事：把新增区间喂进流式通道，同时记下时间基准。
        """
        if not addr or not mem.valid(addr, 1):
            return
        if self._ring_last is None:
            self._ring_last = addr
            self._ring_base = addr
            self._ring_t0 = time.monotonic()
            return
        if addr > self._ring_last:
            n = min(addr - self._ring_last, 64 << 10)     # 单次最多取 64KB
            data = mem.read(self._ring_last, n)
            if data and self.ok:
                self.feed_pcm(data)
                self.ring_bytes += len(data)
        self._ring_last = addr

    def ring_played_ptr(self) -> int:
        """mr_plat(103)：已播放到的绝对地址，按 PCM 字节速率推进。"""
        if self._ring_last is None:
            return 0
        bps = self.pcm_rate * 2 * self.pcm_channels       # 16bit
        elapsed = max(0.0, time.monotonic() - self._ring_t0)
        return (self._ring_base + int(elapsed * bps)) & 0xFFFFFFFF

    # ------------------------------------------------------------ 诊断
    def stats(self) -> str:
        head = f"音频: 调用 {self.calls} 次 | 播放 {self.plays} | 失败 {self.failures}"
        if not self.ok:
            return head + " | mixer 不可用（静音）"
        bits = [head, f"缓存 {len(self._cache)} 条"]
        if self.stream is not None:
            bits.append(self.stream.stats())
        if self.media.players or self.media.calls:
            bits.append(self.media.stats())
        return " | ".join(bits)
