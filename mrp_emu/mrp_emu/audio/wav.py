"""WAV/RIFF 解析。

``mr_playSound(MR_SOUND_WAV, data, len, loop)`` 传进来的是**完整的 .wav 文件
字节**（不是裸 PCM）。这里拆出 fmt/data，统一转成 float32 单声道，
剩下的交给 mixer。

裸 PCM（MR_SOUND_PCM）不走这里 —— 那条路是分段流式的，见 stream.py。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np


class WavError(ValueError):
    """数据不是可用的 WAV。"""


@dataclass
class Wav:
    samples: np.ndarray      # float32 单声道 [-1, 1]
    rate: int
    channels: int
    bits: int

    @property
    def duration(self) -> float:
        return len(self.samples) / float(max(1, self.rate))

    def summary(self) -> str:
        return (f"WAV {self.rate}Hz/{self.channels}ch/{self.bits}bit, "
                f"{self.duration:.2f}s")


def _decode_pcm(raw: bytes, bits: int, channels: int) -> np.ndarray:
    """把交错的多声道整数采样转成 float32 单声道。"""
    if bits == 8:                       # WAV 的 8bit 是无符号
        arr = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        mono = (arr - 128.0) / 128.0
    elif bits == 16:
        arr = np.frombuffer(raw, dtype="<i2").astype(np.float32)
        mono = arr / 32768.0
    elif bits == 24:
        b = np.frombuffer(raw, dtype=np.uint8)
        n = len(b) // 3
        b = b[: n * 3].reshape(n, 3).astype(np.int32)
        val = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        val = np.where(val & 0x800000, val - 0x1000000, val).astype(np.float32)
        mono = val / 8388608.0
    elif bits == 32:
        arr = np.frombuffer(raw, dtype="<i4").astype(np.float32)
        mono = arr / 2147483648.0
    else:
        raise WavError(f"不支持的位深：{bits}")

    if channels > 1:
        n = (len(mono) // channels) * channels
        mono = mono[:n].reshape(-1, channels).mean(axis=1)
    return mono.astype(np.float32)


def parse(data: bytes) -> Wav:
    """解析 WAV。失败抛 WavError。"""
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise WavError(f"不是 RIFF/WAVE：{data[:12]!r}")

    pos = 12
    fmt: tuple[int, int, int, int] | None = None      # (format, channels, rate, bits)
    payload: bytes | None = None

    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        clen = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        body = pos + 8
        end = min(body + clen, len(data))

        if cid == b"fmt " and clen >= 16:
            afmt, ch, rate = struct.unpack("<HHI", data[body:body + 8])
            bits = struct.unpack("<H", data[body + 14:body + 16])[0]
            # 0xFFFE = WAVE_FORMAT_EXTENSIBLE，子格式在 cbSize 之后，取有效位深
            if afmt == 0xFFFE and clen >= 40:
                bits = struct.unpack("<H", data[body + 18:body + 20])[0] or bits
                afmt = struct.unpack("<H", data[body + 24:body + 26])[0]
            fmt = (afmt, max(1, ch), max(1, rate), max(8, bits))
        elif cid == b"data":
            payload = data[body:end]
            if fmt is not None:
                break

        pos = body + clen
        if clen & 1:                                  # chunk 对齐到偶数
            pos += 1

    if fmt is None:
        raise WavError("缺少 fmt 块")
    if payload is None:
        raise WavError("缺少 data 块")

    afmt, channels, rate, bits = fmt
    if afmt == 3 and bits == 32:                      # IEEE float
        arr = np.frombuffer(payload, dtype="<f4").astype(np.float32)
        if channels > 1:
            n = (len(arr) // channels) * channels
            arr = arr[:n].reshape(-1, channels).mean(axis=1)
        mono = np.clip(arr, -1.0, 1.0)
    elif afmt in (1, 3):
        mono = _decode_pcm(payload, bits, channels)
    else:
        # ADPCM / mu-law / a-law 等：老 MRP 极少用，明确报错好过静默出错音
        raise WavError(f"不支持的 WAV 编码（format={afmt}）")

    if mono.size == 0:
        raise WavError("data 块为空")
    return Wav(samples=mono, rate=rate, channels=channels, bits=bits)


def resample(x: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """线性插值重采样。手机音源多是 8k/11k/22k，目标 44.1k。"""
    if src_rate <= 0 or dst_rate <= 0 or src_rate == dst_rate or x.size == 0:
        return x
    n_out = max(1, int(round(x.size * dst_rate / float(src_rate))))
    if x.size == 1:
        return np.full(n_out, x[0], dtype=np.float32)
    idx = np.linspace(0.0, x.size - 1.0, n_out, dtype=np.float32)
    lo = np.floor(idx).astype(np.int32)
    hi = np.minimum(lo + 1, x.size - 1)
    frac = (idx - lo).astype(np.float32)
    out = x[lo] * (1.0 - frac) + x[hi] * frac
    return out.astype(np.float32)
