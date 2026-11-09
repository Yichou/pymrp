#!/usr/bin/env python3
"""音频自检：SMF 解析 / 波表合成 / WAV / 流式 PCM / mr_platEx 播放器。

分两层验证：
  · 纯 Python 层：解析器、合成器、缓存、状态机
  · ARM 端到端：用硬编码 ARM 机器码调 mr_table 槽位（0x094 mr_plat、
    0x098 mr_platEx、0x0E4 mr_playSound），等于人工当一次 cfunction.ext
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pygame  # noqa: E402

pygame.init()

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP  # noqa: E402

from mrp_emu.api.dsmfuncs import DSM_FUNCS  # noqa: E402
from mrp_emu.api.mrtable import MR_TABLE  # noqa: E402
from mrp_emu.app import App  # noqa: E402
from mrp_emu.audio import midi as midi_mod  # noqa: E402
from mrp_emu.audio import synth, wav as wav_mod  # noqa: E402
from mrp_emu.consts import (  # noqa: E402
    MEDIA_MIDI,
    MEDIA_PCM,
    MEDIA_WAVE,
    MR_MEDIA_IDLE,
    MR_MEDIA_LOADED,
    MR_MEDIA_PLAYING,
    MR_PLAT_VALUE_BASE,
    MR_SOUND_MIDI,
    MR_SOUND_PCM,
    MR_SOUND_WAV,
    MR_SUCCESS,
)
from mrp_emu.vm import Vm  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        FAILS.append(name)


# ---------------------------------------------------------------- 测试素材
def vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def build_midi(notes=(60, 64, 67), ticks=96, division=96) -> bytes:
    """造一个最小的 format-0 SMF：三个四分音符。"""
    trk = b""
    for pitch in notes:
        trk += b"\x00" + bytes([0x90, pitch, 100])          # note on
        trk += vlq(ticks) + bytes([0x80, pitch, 64])        # note off
    trk += b"\x00\xFF\x2F\x00"                              # end of track
    head = b"MThd" + struct.pack(">IHHH", 6, 0, 1, division)
    return head + b"MTrk" + struct.pack(">I", len(trk)) + trk


def build_midi_drum() -> bytes:
    """带鼓通道（ch9）的 MIDI，验证打击乐分支。"""
    trk = b""
    for pitch in (36, 38, 42):
        trk += b"\x00" + bytes([0x99, pitch, 110])
        trk += vlq(48) + bytes([0x89, pitch, 0])
    trk += b"\x00\xFF\x2F\x00"
    head = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 96)
    return head + b"MTrk" + struct.pack(">I", len(trk)) + trk


def build_wav(seconds: float = 0.3, rate: int = 8000, freq: int = 440,
              channels: int = 1) -> bytes:
    """造一个 16bit PCM WAV。"""
    n = int(rate * seconds)
    t = np.arange(n, dtype=np.float32) / rate
    mono = (np.sin(2 * np.pi * freq * t) * 0.5 * 32767).astype("<i2")
    data = np.repeat(mono, channels).tobytes() if channels > 1 else mono.tobytes()
    block_align = 2 * channels
    fmt = b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate,
                                rate * block_align, block_align, 16)
    body = b"WAVE" + fmt + b"data" + struct.pack("<I", len(data)) + data
    return b"RIFF" + struct.pack("<I", len(body)) + body


def main() -> int:
    logs: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="mrp_audio_"))

    # ============================================================ 1. 解析
    print("\n== 1. SMF 解析 ==")
    midi_bytes = build_midi()
    song = midi_mod.parse(midi_bytes)
    check("解析出 3 个音符", len(song.notes) == 3, f"实际 {len(song.notes)}")
    check("音高正确", [n.pitch for n in song.notes] == [60, 64, 67],
          str([n.pitch for n in song.notes]))
    # division=96, tempo=500000us → 每 tick 5.208ms，96 tick = 0.5s
    check("首音符时长 0.5s", abs(song.notes[0].dur - 0.5) < 0.02,
          f"= {song.notes[0].dur:.3f}s")
    check("总时长 1.5s", abs(song.duration - 1.5) < 0.05, f"= {song.duration:.3f}s")
    check("BPM 120", abs(song.bpm - 120) < 1, f"= {song.bpm:.1f}")
    check("起始时间递增", song.notes[1].start > song.notes[0].start,
          f"{song.notes[0].start:.2f} → {song.notes[1].start:.2f}")

    drum = midi_mod.parse(build_midi_drum())
    check("鼓通道识别为 ch9", all(n.channel == 9 for n in drum.notes),
          str({n.channel for n in drum.notes}))

    # 容错
    try:
        midi_mod.parse(b"not a midi at all")
        check("非法数据被拒", False)
    except midi_mod.MidiError:
        check("非法数据被拒", True)

    # ============================================================ 2. 合成
    print("\n== 2. 波表合成 ==")
    pcm = synth.render(song, 44100)
    # render 会在末尾留一小段释放尾巴，所以长度略大于 1.5s
    check("PCM 长度覆盖 1.5s 且不过长", 1.5 <= len(pcm) / 44100 <= 1.9,
          f"= {len(pcm) / 44100:.2f}s")
    peak = float(np.max(np.abs(pcm)))
    check("波形非静音", peak > 0.05, f"peak={peak:.3f}")
    check("不削顶（|x| ≤ 1）", peak <= 1.0, f"peak={peak:.3f}")
    rms = float(np.sqrt(np.mean(pcm ** 2)))
    check("RMS 合理（有声但不满）", 0.02 < rms < 0.6, f"rms={rms:.3f}")

    pcm2 = synth.render(song, 44100)
    check("渲染确定性（同输入同输出）", np.array_equal(pcm, pcm2))

    drum_pcm = synth.render(drum, 44100)
    check("鼓声也非静音", float(np.max(np.abs(drum_pcm))) > 0.05,
          f"peak={float(np.max(np.abs(drum_pcm))):.3f}")

    # 不同音色要真的不同
    a = synth.render(midi_mod.parse(build_midi(notes=(60,))), 44100)
    b_midi = midi_mod.parse(build_midi(notes=(72,)))
    b = synth.render(b_midi, 44100)
    check("不同音高波形不同", not np.array_equal(a[:4000], b[:4000]))

    # 走音检查：单音渲染后做 FFT，主频必须对得上十二平均律
    def dominant_hz(buf: np.ndarray, sr: int = 44100) -> float:
        seg = buf[: int(0.3 * sr)]
        if seg.size < 64:
            return 0.0
        seg = seg * np.hanning(seg.size)
        spec = np.abs(np.fft.rfft(seg))
        freqs = np.fft.rfftfreq(seg.size, 1.0 / sr)
        band = freqs > 40.0
        return float(freqs[band][np.argmax(spec[band])])

    worst = 0.0
    detail = []
    for pitch in (60, 69, 72, 84):
        expect = 440.0 * 2 ** ((pitch - 69) / 12.0)
        got = dominant_hz(synth.render(midi_mod.parse(build_midi(notes=(pitch,), ticks=192)), 44100))
        cents = abs(1200.0 * np.log2(got / expect)) if got > 0 else 9999
        worst = max(worst, cents)
        detail.append(f"{pitch}:{got:.0f}Hz")
    check("音高准确（偏差 < 50 音分）", worst < 50.0,
          f"最大 {worst:.0f} 分 | " + " ".join(detail))

    # ============================================================ 3. WAV
    print("\n== 3. WAV 解析 ==")
    wav_bytes = build_wav(0.3, 8000, 440)
    w = wav_mod.parse(wav_bytes)
    check("WAV 采样率 8000", w.rate == 8000, f"= {w.rate}")
    check("WAV 时长 0.3s", abs(w.duration - 0.3) < 0.01, f"= {w.duration:.3f}s")
    check("WAV 单声道", w.channels == 1)
    check("WAV 有声音", float(np.max(np.abs(w.samples))) > 0.3,
          f"peak={float(np.max(np.abs(w.samples))):.2f}")

    up = wav_mod.resample(w.samples, 8000, 44100)
    check("重采样 8k→44.1k 长度正确",
          abs(len(up) / 44100 - 0.3) < 0.01, f"= {len(up) / 44100:.3f}s")

    stereo_wav = wav_mod.parse(build_wav(0.2, 16000, 440, channels=2))
    check("立体声下混为单声道", stereo_wav.channels == 2 and stereo_wav.samples.ndim == 1,
          f"ch={stereo_wav.channels}, dim={stereo_wav.samples.ndim}")

    try:
        wav_mod.parse(b"RIFFxxxxWAVEbad")
        check("非法 WAV 被拒", False)
    except wav_mod.WavError:
        check("非法 WAV 被拒", True)

    # ============================================================ 4. 引擎
    print("\n== 4. AudioEngine ==")
    vm = Vm(log=logs.append)
    app = App(vm, tmp, log=logs.append, audio=True)
    vm.app = app
    vm.install_tables(MR_TABLE, DSM_FUNCS)
    audio = app.audio
    check("mixer 初始化", audio.ok, f"{audio.sample_rate}Hz/{audio.channels}ch")

    r = audio.play(MR_SOUND_MIDI, midi_bytes, False)
    check("播放 MIDI 返回成功", r == MR_SUCCESS, f"= {r}")
    check("渲染出非空 PCM", len(audio.last_pcm) > 10000, f"{len(audio.last_pcm)}B")
    check("渲染耗时合理", audio.render_ms < 3000, f"{audio.render_ms:.0f}ms")

    cached_before = len(audio._cache)
    audio.play(MR_SOUND_MIDI, midi_bytes, False)
    check("重复播放命中缓存", len(audio._cache) == cached_before,
          f"缓存 {len(audio._cache)} 条")

    r = audio.play(MR_SOUND_WAV, wav_bytes, False)
    check("播放 WAV 返回成功", r == MR_SUCCESS, f"= {r}")

    audio.stop(MR_SOUND_MIDI)
    check("stop MIDI 不抛异常", True)

    r = audio.play(MR_SOUND_MIDI, b"", False)
    check("空数据返回失败", r != MR_SUCCESS, f"= {r}")

    # PCM 流（type 3 = vmrp 的 PCM）
    tone = (np.sin(2 * np.pi * 440 * np.arange(800) / 8000) * 12000).astype("<i2")
    for _ in range(30):                                # 30 块 × 100ms = 3s
        audio.play(MR_SOUND_PCM, tone.tobytes(), False)
    st = audio.stream
    check("PCM 流已建立", st is not None)
    if st is not None:
        check("PCM 流累计数据量正确", st.fed_bytes == 30 * tone.nbytes,
              f"{st.fed_bytes}B")
        check("PCM 流推到播放块", st.played_chunks > 0, f"{st.played_chunks} 块")
        audio.stop(MR_SOUND_PCM)
        check("PCM 流可停止", not st.active)

    # AMR 数据不能被误当 PCM
    amr = b"#!AMR\n" + b"\x00" * 100
    r = audio.play(MR_SOUND_PCM, amr, False)
    check("AMR 数据被识别出来（不误当 PCM）", r != MR_SUCCESS, f"= {r}")

    # ============================================================ 5. ARM 端到端
    print("\n== 5. ARM 端到端（mr_playSound 槽位 0x0E4） ==")

    def run_arm(code_words: list[int], extra: list[int], stop_off: int) -> None:
        blob = b"".join(struct.pack("<I", w) for w in code_words + extra)
        addr = 0x90000
        vm.mem.write(addr, blob)
        sp = vm.uc.reg_read(UC_ARM_REG_SP)
        vm.uc.emu_start(addr, addr + stop_off, 0, 0)
        vm.uc.reg_write(UC_ARM_REG_SP, sp)

    audio._cache.clear()
    audio.calls = 0
    audio.plays = 0

    data_addr = vm.mem.malloc(len(midi_bytes))
    vm.mem.write(data_addr, midi_bytes)
    slot_play = vm.mr_table + 0x0E4

    # ldr r0..r3 = (type, data, len, loop); ldr r4 = slot; blx r4
    # 5 条 ldr 都指向数据区（PC=指令地址+8 → 数据区在 +0x14）
    run_arm(
        [0xE59F0014,          # ldr r0, [pc, #0x14]  type
         0xE59F1014,          # ldr r1, [pc, #0x14]  data
         0xE59F2014,          # ldr r2, [pc, #0x14]  len
         0xE59F3014,          # ldr r3, [pc, #0x14]  loop
         0xE59F4014,          # ldr r4, [pc, #0x14]  slot
         0xE12FFF34,          # blx r4
         0xEAFFFFFE],         # b .
        [MR_SOUND_MIDI, data_addr, len(midi_bytes), 0, slot_play],
        stop_off=0x18,
    )
    ret = vm.uc.reg_read(UC_ARM_REG_R0)
    check("mr_playSound 返回 MR_SUCCESS", ret == MR_SUCCESS, f"= {ret}")
    check("引擎收到调用", audio.calls >= 1, f"calls={audio.calls}")
    check("引擎真的渲染了", len(audio.last_pcm) > 10000, f"{len(audio.last_pcm)}B")

    # 循环播放
    run_arm(
        [0xE59F0014, 0xE59F1014, 0xE59F2014, 0xE59F3014, 0xE59F4014,
         0xE12FFF34, 0xEAFFFFFE],
        [MR_SOUND_MIDI, data_addr, len(midi_bytes), 1, slot_play],
        stop_off=0x18,
    )
    check("loop=1 传达到播放器", "循环" in audio.last_desc, audio.last_desc[:40])

    # mr_stopSound 槽位 0x0E8（4 条指令=16B，数据区在 +0x10，PC=指令+8）
    run_arm(
        [0xE3A00000,          # mov r0, #0  (MR_SOUND_MIDI)
         0xE59F3004,          # ldr r3, [pc, #4]
         0xE12FFF33,          # blx r3
         0xEAFFFFFE],
        [vm.mr_table + 0x0E8],
        stop_off=0x0C,
    )
    check("mr_stopSound 返回成功", vm.uc.reg_read(UC_ARM_REG_R0) == MR_SUCCESS)

    # ============================================================ 6. mr_platEx
    print("\n== 6. mr_platEx 流媒体播放器 ==")
    slot_platEx = vm.mr_table + 0x098
    slot_plat = vm.mr_table + 0x094

    # 6 参数：r0=code r1=input r2=input_len r3=output，r4 以上的走栈
    ARG5 = 0x91000
    ARG6 = 0x91004
    OUTBUF = 0x91100
    OUTLEN = 0x91104
    REQ = 0x91200                                   # LOAD_AUDIO_DATA_REQ
    TMP = 0x91300                                   # T_SET_PLAY_POS / T_MEDIA_TIME

    def plat_ex(code: int, input_addr: int = 0, input_len: int = 0) -> int:
        run_arm(
            [0xE59F0024,      # ldr r0, [pc, #0x24]  code
             0xE59F1024,      # ldr r1, ...           input
             0xE59F2024,      # ldr r2, ...           input_len
             0xE59F3024,      # ldr r3, ...           output
             0xE59F6024,      # ldr r6, ...           output_len
             0xE59F5024,      # ldr r5, ...           slot
             0xE24DD008,      # sub sp, sp, #8
             0xE58D6000,      # str r6, [sp]
             0xE58D6004,      # str r6, [sp, #4]
             0xE12FFF35,      # blx r5
             0xEAFFFFFE],     # b .
            [code, input_addr, input_len, OUTBUF, OUTLEN, slot_platEx],
            stop_off=0x28,
        )
        return vm.uc.reg_read(UC_ARM_REG_R0) & 0xFFFFFFFF

    def plat(code: int, param: int) -> int:
        # 5 条指令 = 20B，数据区在 +0x14；PC = 指令地址 + 8 → 偏移 0x0C
        run_arm(
            [0xE59F000C,      # ldr r0, [pc, #12]  code
             0xE59F100C,      # ldr r1, [pc, #12]  param
             0xE59F300C,      # ldr r3, [pc, #12]  slot
             0xE12FFF33,      # blx r3
             0xEAFFFFFE],     # b .
            [code, param, slot_plat],
            stop_off=0x10,        # 最后一条 b . 的地址（5 条指令）
        )
        return vm.uc.reg_read(UC_ARM_REG_R0) & 0xFFFFFFFF

    p = audio.media.player(MEDIA_MIDI)

    r = plat_ex(2011)                               # 201x + MEDIA_MIDI
    check("2011 设备初始化", r == MR_SUCCESS, f"= {r}")
    check("状态 → INITED", p.state == 1002, f"= {p.state}")

    vm.mem.set_u32(REQ, data_addr)
    vm.mem.set_u32(REQ + 4, len(midi_bytes))
    r = plat_ex(2031, REQ, 8)                       # 203x 加载缓冲
    check("2031 加载内存缓冲", r == MR_SUCCESS, f"= {r}")
    check("状态 → LOADED", p.state == MR_MEDIA_LOADED, f"= {p.state}")
    check("解析出时长 1.5s", abs(p.duration - 1.5) < 0.1, f"= {p.duration:.2f}s")

    r = plat_ex(2041)                               # 204x 播放
    check("2041 播放", r == MR_SUCCESS, f"= {r}")
    check("状态 → PLAYING", p.state == MR_MEDIA_PLAYING, f"= {p.state}")

    r = plat_ex(2091)                               # 209x 状态
    check("2091 返回 PLAT_VALUE_BASE + PLAYING",
          r == MR_PLAT_VALUE_BASE + MR_MEDIA_PLAYING, f"= {r}")

    r = plat_ex(2121, 0, 0)                         # 212x 总时长（output 结构）
    out_addr = vm.mem.u32(OUTBUF) if r == MR_SUCCESS else 0
    total = vm.mem.s32(out_addr) if out_addr else -1
    check("2121 总时长写入结构体", r == MR_SUCCESS and abs(total - 1) <= 1,
          f"ret={r}, pos={total}s")
    check("2121 写了 output_len=4", vm.mem.u32(OUTLEN) == 4, f"= {vm.mem.u32(OUTLEN)}")

    r = plat_ex(2131, 0, 0)                         # 213x 当前进度
    check("2131 当前进度可读", r == MR_SUCCESS, f"= {r}")

    vm.mem.set_u32(TMP, 1)
    r = plat_ex(2101, TMP, 4)                       # 210x 定位到 1 秒
    check("2101 定位到 1s", r == MR_SUCCESS, f"= {r}")
    check("定位后进度 ≥ 1s", p.position() >= 0.95, f"{p.position():.2f}s")

    r = plat_ex(2051)                               # 205x 暂停
    check("2051 暂停", r == MR_SUCCESS and p.state == 1005, f"= {p.state}")
    frozen = p.position()
    r = plat_ex(2061)                               # 206x 继续
    check("2061 继续", r == MR_SUCCESS and p.state == MR_MEDIA_PLAYING,
          f"= {p.state}")
    check("继续后进度不倒退", p.position() >= frozen - 0.1,
          f"{frozen:.2f} → {p.position():.2f}")

    r = plat_ex(2071)                               # 207x 停止
    check("2071 停止", r == MR_SUCCESS and p.state == MR_MEDIA_LOADED,
          f"= {p.state}")

    r = plat_ex(2161)                               # 216x 释放
    check("2161 释放", r == MR_SUCCESS and p.state == MR_MEDIA_IDLE,
          f"= {p.state}")

    # 不支持的类型应返回 MR_IGNORE，而不是崩
    r = plat_ex(2043)                               # MP3 播放（未加载）
    check("不支持的类型安全返回", r in (1, 0xFFFFFFFF), f"= {r}")

    # 多通道 222x：T_BG_PLAY_REQ { data, len, loop }
    BG = 0x91400
    vm.mem.set_u32(BG, data_addr)
    vm.mem.set_u32(BG + 4, len(midi_bytes))
    vm.mem.set_u32(BG + 8, 0)
    r = plat_ex(2221, BG, 12)
    check("2221 多通道加载返回句柄", r >= 1, f"handle={r}")
    handle = r
    vm.mem.set_u32(TMP, handle)
    r = plat_ex(2231, TMP, 4)
    check("2231 多通道播放", r == MR_SUCCESS, f"= {r}")
    r = plat_ex(2241, TMP, 4)
    check("2241 多通道停止", r == MR_SUCCESS, f"= {r}")
    r = plat_ex(2251, TMP, 4)
    check("2251 多通道释放", r == MR_SUCCESS, f"= {r}")

    # ============================================================ 7. PCM 环形缓冲
    print("\n== 7. mr_plat(102/103) PCM 环形缓冲 ==")
    RING = 0x92000
    pcm_tone = (np.sin(2 * np.pi * 440 * np.arange(2000) / 8000) * 10000).astype("<i2")
    vm.mem.write(RING, pcm_tone.tobytes())

    audio.ring_bytes = 0
    r = plat(102, RING + 2000)                      # 第一次：建立基准
    check("102 首次登记成功", r == MR_SUCCESS, f"= {r}")
    r = plat(102, RING + 4000)                      # 增量
    check("102 增量登记成功", r == MR_SUCCESS, f"= {r}")
    check("环形缓冲数据喂进了流", audio.ring_bytes > 0, f"{audio.ring_bytes}B")

    played = plat(103, 0)
    check("103 返回播放位置", played >= RING, f"0x{played:X}")

    # ============================================================ 8. 音量
    print("\n== 8. 音量控制 ==")
    r = plat(1302, 8)
    check("1302 设置音量成功", r == MR_SUCCESS, f"= {r}")
    check("音量落在 0..1", 0.0 <= audio.volume <= 1.0, f"= {audio.volume:.2f}")

    # ============================================================ 汇总
    print("\n== 摘要 ==")
    print(f"  {audio.stats()}")
    for line in logs[-4:]:
        print("      " + line)
    print(f"\n  失败 {len(FAILS)} 项" + ("" if not FAILS else "：" + ", ".join(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
