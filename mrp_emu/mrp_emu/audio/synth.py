"""把 Midi 渲染成 PCM —— numpy 波表合成。

MTK 手机当年是硬件 MIDI 合成（和弦铃声），复音数和采样率都很有限。这里
按 GM 音色家族挑波形和 ADSR 包络做近似，目标不是 HiFi，而是：
能听出旋律、不刺耳、CPU 便宜、headless 下也能跑。

输出是 float32 单声道 [-1, 1]。当年手机就是单声道喇叭，所以不做立体声。
"""

from __future__ import annotations

import numpy as np

from .midi import Midi, Note

TWO_PI = 2.0 * np.pi
_MIN_FREQ = 20.0
_MAX_FREQ = 11000.0


# ---------------------------------------------------------------- 音色
# (波形, attack, decay, sustain, release)  —— 时间单位秒
_PIANO = ("sine", 0.004, 0.35, 0.16, 0.28)
_BELL = ("sine", 0.002, 0.22, 0.04, 0.20)
_ORGAN = ("organ", 0.010, 0.02, 0.88, 0.08)
_GUITAR = ("saw", 0.004, 0.30, 0.10, 0.22)
_BASS = ("bass", 0.004, 0.20, 0.62, 0.09)
_STRINGS = ("saw", 0.055, 0.10, 0.76, 0.28)
_ENSEMBLE = ("saw", 0.075, 0.10, 0.80, 0.32)
_BRASS = ("saw", 0.028, 0.08, 0.74, 0.12)
_REED = ("square", 0.020, 0.06, 0.80, 0.10)
_PIPE = ("sine", 0.030, 0.05, 0.85, 0.15)
_LEAD = ("square", 0.005, 0.10, 0.70, 0.10)
_PAD = ("tri", 0.150, 0.20, 0.80, 0.40)
_FX = ("sine", 0.006, 0.30, 0.30, 0.30)
_ETHNIC = ("saw", 0.006, 0.25, 0.20, 0.18)
_PERC = ("noise", 0.001, 0.10, 0.02, 0.10)


def _voice(program: int) -> tuple[str, float, float, float, float]:
    """GM program(0-127) → 音色参数。按 8 个音色一组归类，够用了。"""
    if program < 0:
        program = 0
    p = program & 0x7F
    if p < 8:
        return _PIANO
    if p < 16:
        return _BELL
    if p < 24:
        return _ORGAN
    if p < 32:
        return _GUITAR
    if p < 40:
        return _BASS
    if p < 48:
        return _STRINGS
    if p < 56:
        return _ENSEMBLE
    if p < 64:
        return _BRASS
    if p < 72:
        return _REED
    if p < 80:
        return _PIPE
    if p < 88:
        return _LEAD
    if p < 96:
        return _PAD
    if p < 104:
        return _FX
    if p < 112:
        return _ETHNIC
    return _PERC


# ---------------------------------------------------------------- 波形
def _osc(kind: str, freq: float, n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n, dtype=np.float32) / np.float32(sr)
    phase = np.mod(freq * t, 1.0)

    if kind == "sine":
        return np.sin(TWO_PI * phase).astype(np.float32)
    if kind == "tri":
        return (4.0 * np.abs(phase - 0.5) - 1.0).astype(np.float32)
    if kind == "square":
        w = np.where(phase < 0.5, 1.0, -1.0).astype(np.float32)
        return _soften(w, sr, freq)
    if kind == "saw":
        w = (2.0 * phase - 1.0).astype(np.float32)
        return _soften(w, sr, freq)
    if kind == "organ":                        # 正弦 + 八度泛音，接近风琴
        return (np.sin(TWO_PI * phase)
                + 0.45 * np.sin(TWO_PI * 2.0 * phase)
                + 0.22 * np.sin(TWO_PI * 3.0 * phase)).astype(np.float32) / 1.67
    if kind == "bass":                         # 低频正弦 + 一点方波增加轮廓
        return (np.sin(TWO_PI * phase)
                + 0.30 * np.sign(np.sin(TWO_PI * phase))).astype(np.float32) / 1.30
    if kind == "noise":
        return rng.uniform(-1.0, 1.0, n).astype(np.float32)
    return np.sin(TWO_PI * phase).astype(np.float32)


def _soften(wave: np.ndarray, sr: int, freq: float) -> np.ndarray:
    """移动平均充当低通：削掉锯齿/方波最扎耳的高频边角。

    没有 scipy，也不用逐样本递推（几十万样本的 Python 循环会拖死主线程）。
    核长按音高取 1-4 点，np.convolve 是 O(n·k)，很快。
    """
    k = int(min(4, max(1, round(freq * 8.0 / sr))))
    if k <= 1:
        return wave
    kernel = np.ones(k, dtype=np.float32) / np.float32(k)
    return np.convolve(wave, kernel, mode="same").astype(np.float32)


# ---------------------------------------------------------------- 包络
def _envelope(n: int, sr: int, a: float, d: float, s: float, r: float) -> np.ndarray:
    """简化 ADSR：起音 → 衰减到延音电平 → 保持 → 释放。"""
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    na = max(1, int(a * sr))
    nd = max(1, int(d * sr))
    nr = max(1, int(r * sr))
    total = na + nd + nr
    if total > n:                              # 音符太短，按比例压缩三段
        scale = n / float(total)
        na = max(1, int(na * scale))
        nd = max(1, int(nd * scale))
        nr = max(1, n - na - nd)
        if nr < 1:
            nr = 1
    ns = max(0, n - na - nd - nr)

    env = np.empty(n, dtype=np.float32)
    i = 0
    env[i:i + na] = np.linspace(0.0, 1.0, na, dtype=np.float32)
    i += na
    env[i:i + nd] = np.linspace(1.0, s, nd, dtype=np.float32)
    i += nd
    if ns:
        env[i:i + ns] = s
        i += ns
    take = min(nr, n - i)
    if take > 0:
        env[i:i + take] = np.linspace(s, 0.0, take, dtype=np.float32)
    return env


# ---------------------------------------------------------------- 鼓
def _drum(pitch: int, n: int, sr: int, rng: np.random.Generator,
          vel: float) -> np.ndarray:
    """通道 10 的打击乐：底鼓、军鼓、踩镲、嗵鼓、吊镲。"""
    t = np.arange(n, dtype=np.float32) / np.float32(sr)
    noise = rng.uniform(-1.0, 1.0, n).astype(np.float32)

    if pitch in (35, 36):                      # 底鼓：扫频正弦
        f = np.linspace(120.0, 44.0, n, dtype=np.float32)
        phase = np.cumsum(f) / np.float32(sr)
        body = np.sin(TWO_PI * phase).astype(np.float32)
        env = np.exp(-t * 11.0).astype(np.float32)
        return (body * env * 1.1).astype(np.float32)

    if pitch in (38, 40):                      # 军鼓：噪声 + 一点音高
        env = np.exp(-t * 22.0).astype(np.float32)
        body = np.sin(TWO_PI * 190.0 * t).astype(np.float32) * 0.35
        return ((noise * 0.9 + body) * env).astype(np.float32)

    if pitch in (42, 44, 46, 51, 54, 56, 69, 70, 75, 76):   # 踩镲
        env = np.exp(-t * 55.0).astype(np.float32)
        hp = noise - np.roll(noise, 1)          # 一阶差分 ≈ 高通，做出"嚓"的质感
        return (hp * env * 0.45).astype(np.float32)

    if pitch in (49, 52, 55, 57, 58, 59):      # 吊镲
        env = np.exp(-t * 7.0).astype(np.float32)
        return ((noise - np.roll(noise, 2)) * env * 0.35).astype(np.float32)

    if 41 <= pitch <= 50:                       # 嗵鼓：按音高扫频
        base = 90.0 + (50 - pitch) * 8.0
        f = np.linspace(base * 1.6, base, n, dtype=np.float32)
        phase = np.cumsum(f) / np.float32(sr)
        env = np.exp(-t * 16.0).astype(np.float32)
        return (np.sin(TWO_PI * phase).astype(np.float32) * env * 0.95)

    # 其它打击乐统一走短噪声
    env = np.exp(-t * 30.0).astype(np.float32)
    return (noise * env * 0.4).astype(np.float32)


# ---------------------------------------------------------------- 渲染
def render(midi: Midi, sample_rate: int = 44100,
           max_seconds: float = 120.0) -> np.ndarray:
    """把 Midi 渲染成 float32 单声道 PCM。

    max_seconds 是保护闸：损坏的 MIDI 可能解出几小时的时长，直接截断。
    """
    sr = int(sample_rate)
    dur = min(float(midi.duration), float(max_seconds))
    total = max(1, int(dur * sr) + int(0.25 * sr))
    buf = np.zeros(total, dtype=np.float32)
    rng = np.random.default_rng(0x4D52_5001)   # 固定种子：同样输入 → 同样输出

    for note in midi.notes:
        if note.start >= dur:
            continue
        params = _voice(note.program)
        kind, a, d, s, r = params

        # 释放段已经在包络里，pcm 长度按 dur + 一点点尾巴
        n = int(min(note.dur, dur - note.start) * sr)
        if n < 8:
            continue
        tail = min(int(0.08 * sr), total - int(note.start * sr) - n)
        n += max(0, tail)
        start = int(note.start * sr)
        if start >= total:
            continue
        n = min(n, total - start)
        if n < 8:
            continue

        vel = max(1, min(127, note.velocity)) / 127.0
        gain = (vel ** 1.3) * 0.30

        if note.channel == 9:
            wave = _drum(note.pitch, n, sr, rng, vel)
            env = np.ones(n, dtype=np.float32) * gain * 1.6
        else:
            freq = 440.0 * (2.0 ** ((note.pitch - 69) / 12.0))
            freq = max(_MIN_FREQ, min(_MAX_FREQ, freq))
            wave = _osc(kind, freq, n, sr, rng)
            env = _envelope(n, sr, a, d, s, r) * gain

        buf[start:start + n] += wave * env

    # 软削波：多音符叠加后不炸耳朵，也不出现数字削顶
    peak = float(np.max(np.abs(buf))) if total else 0.0
    if peak > 0.001:
        buf = np.tanh(buf * (1.05 / peak)).astype(np.float32) * 0.92
    return buf


def to_pcm16(buf: np.ndarray) -> bytes:
    """float32 [-1,1] → 16bit 小端 PCM 字节串（pygame.mixer.Sound 吃这个）。"""
    clipped = np.clip(buf, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()


def to_stereo16(buf: np.ndarray, channels: int = 2) -> bytes:
    """单声道 float32 → N 声道 16bit PCM（mixer 初始化成双声道时用）。"""
    data = to_pcm16(buf)
    if channels <= 1:
        return data
    mono = np.frombuffer(data, dtype="<i2")
    return np.repeat(mono, channels).astype("<i2").tobytes()
