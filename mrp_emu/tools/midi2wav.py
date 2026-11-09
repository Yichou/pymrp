#!/usr/bin/env python3
"""把 .mid / .imy / .wav 转成 .wav，用来听模拟器的声音渲染结果。

    python tools/midi2wav.py song.mid              # → song.wav
    python tools/midi2wav.py song.mid -o out.wav
    python tools/midi2wav.py --demo                # 生成一段测试旋律

这个工具走的是和模拟器内部完全相同的代码路径（audio/midi.py 解析 +
audio/synth.py 合成），所以听到的就是 MRP 在模拟器里听到的效果。
"""

from __future__ import annotations

import argparse
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from mrp_emu.audio import midi as midi_mod  # noqa: E402
from mrp_emu.audio import synth  # noqa: E402


def write_wav(path: Path, samples: np.ndarray, rate: int = 44100) -> None:
    data = (np.clip(samples, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data)


def vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def demo_midi() -> bytes:
    """一段 C 大调琶音 + 简单和弦，用来判断合成器是否走音。"""
    # (音高, 起始tick, 时长tick)
    notes = [
        (60, 0, 96), (64, 96, 96), (67, 192, 96), (72, 288, 192),
        (67, 480, 96), (72, 576, 96), (76, 672, 192),
        (60, 864, 96), (64, 864, 96), (67, 864, 96),      # C 和弦
        (65, 1056, 96), (69, 1056, 96), (72, 1056, 96),   # F 和弦
        (67, 1248, 96), (71, 1248, 96), (74, 1248, 96),   # G 和弦
        (60, 1440, 384),                                  # 收尾 C
    ]
    events: list[tuple[int, int, bytes]] = []
    for pitch, start, dur in notes:
        events.append((start, 1, bytes([0x90, pitch, 96])))
        events.append((start + dur, 0, bytes([0x80, pitch, 64])))
    events.sort(key=lambda e: (e[0], e[1]))

    trk = b""
    last = 0
    for tick, _order, msg in events:
        trk += vlq(tick - last) + msg
        last = tick
    trk += b"\x00\xFF\x2F\x00"

    head = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 96)
    return head + b"MTrk" + struct.pack(">I", len(trk)) + trk


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="把 MIDI/IMY/WAV 渲染成 WAV")
    ap.add_argument("src", nargs="?", help="输入文件（.mid/.midi/.imy/.wav）")
    ap.add_argument("-o", "--output", help="输出 wav 路径")
    ap.add_argument("--rate", type=int, default=44100, help="采样率")
    ap.add_argument("--demo", action="store_true", help="生成内置测试旋律")
    args = ap.parse_args(argv)

    if args.demo:
        data = demo_midi()
        name = "demo.mid"
    elif args.src:
        p = Path(args.src)
        if not p.is_file():
            print(f"找不到文件：{p}")
            return 1
        data = p.read_bytes()
        name = p.name
    else:
        ap.print_help()
        return 1

    ext = name.rsplit(".", 1)[-1].lower()
    try:
        if ext == "wav":
            from mrp_emu.audio import wav as wav_mod
            w = wav_mod.parse(data)
            samples = (w.samples if w.rate == args.rate
                       else wav_mod.resample(w.samples, w.rate, args.rate))
            desc = w.summary()
        else:
            song = midi_mod.load(data)
            samples = synth.render(song, args.rate)
            keep = min(len(samples), int(song.duration * args.rate) + int(0.02 * args.rate))
            samples = samples[:keep]
            desc = song.summary()
    except Exception as exc:  # noqa: BLE001
        print(f"解析失败：{type(exc).__name__}: {exc}")
        return 1

    out = Path(args.output) if args.output else Path(name).with_suffix(".wav")
    write_wav(out, samples, args.rate)

    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    rms = float(np.sqrt(np.mean(samples ** 2))) if samples.size else 0.0
    print(f"{desc}")
    print(f"→ {out}  ({len(samples) / args.rate:.2f}s, peak={peak:.2f}, rms={rms:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
