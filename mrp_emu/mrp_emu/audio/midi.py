"""Standard MIDI File 解析。

MRP 侧的调用是 ``mr_playSound(MR_SOUND_MIDI, data, len, loop)``，data 指向
**内存里的 .mid 原始字节**（应用先 mr_open/mr_read 读出来，或者直接嵌在
代码段里）。所以宿主必须自己解析 SMF —— 这就是本模块的职责。

只解析播放需要的东西：音符、音色、tempo。不碰 sysex、歌词、控制器细化。
解析结果是按秒排好的 Note 列表，交给 synth.py 渲染成 PCM。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field


class MidiError(ValueError):
    """数据不是可用的 MIDI/IMY。"""


# ---------------------------------------------------------------- 数据结构
@dataclass
class Note:
    start: float          # 起始秒
    dur: float            # 时长秒（已含释放）
    pitch: int            # 0-127
    velocity: int         # 0-127
    program: int          # 0-127（鼓通道固定 0）
    channel: int          # 0-15，9 = 鼓


@dataclass
class Midi:
    notes: list[Note] = field(default_factory=list)
    duration: float = 0.0
    name: str = ""
    division: int = 96
    tempo_us: int = 500000     # 初始 tempo（微秒/四分音符）

    @property
    def bpm(self) -> float:
        return 60_000_000.0 / max(1, self.tempo_us)

    def summary(self) -> str:
        return (f"{self.name or 'MIDI'}: {len(self.notes)} 音符, "
                f"{self.duration:.2f}s, {self.bpm:.0f}BPM, div={self.division}")


# ---------------------------------------------------------------- 基础读取
def _vlq(buf: bytes, pos: int) -> tuple[int, int]:
    """MIDI 变长量：每字节低 7 位，最高位表示「还有后续」。"""
    value = 0
    for _ in range(4):
        if pos >= len(buf):
            raise MidiError("VLQ 越界")
        b = buf[pos]
        pos += 1
        value = (value << 7) | (b & 0x7F)
        if not b & 0x80:
            return value, pos
    return value, pos


def _is_smf(data: bytes) -> bool:
    return len(data) >= 14 and data[:4] in (b"MThd", b"RIFF")


# ---------------------------------------------------------------- SMF 解析
class _Merged:
    """把所有轨道的事件拍平，按 (tick, 轨道, 序号) 稳定排序后统一走一遍。"""

    __slots__ = ("tick", "track", "seq", "kind", "a", "b", "c")

    def __init__(self, tick, track, seq, kind, a=0, b=0, c=0) -> None:
        self.tick = tick
        self.track = track
        self.seq = seq
        self.kind = kind
        self.a = a
        self.b = b
        self.c = c

    def key(self):
        return (self.tick, self.track, self.seq)


def _parse_track(buf: bytes, start: int, end: int, track: int, out: list[_Merged]) -> None:
    """解析一个 MTrk 块里的事件，全部塞进 out。"""
    pos = start
    tick = 0
    seq = 0
    running = 0          # running status：省掉重复的状态字节
    while pos < end:
        delta, pos = _vlq(buf, pos)
        tick += delta
        if pos >= end:
            break
        status = buf[pos]

        if status < 0x80:                 # 裸数据 → 沿用上一个状态
            if not running:
                pos += 1                  # 坏数据，跳一个字节继续
                continue
            status = running
        else:
            pos += 1
            if status < 0xF0:
                running = status

        high = status & 0xF0
        chan = status & 0x0F

        if status == 0xFF:                # meta
            if pos >= end:
                break
            mtype = buf[pos]
            pos += 1
            mlen, pos = _vlq(buf, pos)
            body = buf[pos:pos + mlen]
            pos += mlen
            if mtype == 0x51 and mlen >= 3:      # tempo
                us = (body[0] << 16) | (body[1] << 8) | body[2]
                if us > 0:
                    out.append(_Merged(tick, track, seq, "tempo", us))
            elif mtype == 0x03:                  # 轨道名
                try:
                    out.append(_Merged(tick, track, seq, "name",
                                       bytes(body).decode("gbk", "ignore")))
                except Exception:
                    pass
            elif mtype == 0x2F:                  # 轨道结束
                return
            seq += 1
            continue

        if status in (0xF0, 0xF7):        # sysex：只跳过
            slen, pos = _vlq(buf, pos)
            pos += slen
            seq += 1
            continue

        # ---- 通道消息
        if high in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            if pos + 1 >= end:
                break
            d1, d2 = buf[pos], buf[pos + 1]
            pos += 2
            if high == 0x90 and d2 > 0:
                out.append(_Merged(tick, track, seq, "on", chan, d1, d2))
            elif high == 0x80 or (high == 0x90 and d2 == 0):
                out.append(_Merged(tick, track, seq, "off", chan, d1, 0))
            elif high == 0xB0:
                # 7=音量 10=声像 121=重置控制器 123=全部音符关闭
                if d1 == 123:
                    out.append(_Merged(tick, track, seq, "alloff", chan))
                else:
                    out.append(_Merged(tick, track, seq, "ctrl", chan, d1, d2))
            elif high == 0xE0:
                bend = ((d2 << 7) | d1) - 8192
                out.append(_Merged(tick, track, seq, "bend", chan, bend))
            else:
                out.append(_Merged(tick, track, seq, "other", chan, d1, d2))
            seq += 1
            continue

        if high in (0xC0, 0xD0):
            if pos >= end:
                break
            d1 = buf[pos]
            pos += 1
            if high == 0xC0:
                out.append(_Merged(tick, track, seq, "prog", chan, d1))
            seq += 1
            continue

        pos += 1                          # 未知字节，跳掉


def parse(data: bytes) -> Midi:
    """解析 SMF，返回带绝对时间的音符表。失败抛 MidiError。"""
    if len(data) < 14:
        raise MidiError(f"数据太短（{len(data)} 字节）")
    if data[:4] != b"MThd":
        raise MidiError(f"不是 MThd 头：{data[:4]!r}")

    hlen = struct.unpack(">I", data[4:8])[0]
    fmt, ntrks, division = struct.unpack(">HHH", data[8:14])

    # SMPTE 时间格式（高字节为负帧率）：老 MRP 基本不出现，按 25fps 兜底
    if division & 0x8000:
        fps = 256 - (division >> 8)
        ticks_per_frame = division & 0xFF
        ticks_per_second = float(max(1, fps) * max(1, ticks_per_frame))
        ticks_per_qn = None
    else:
        ticks_per_second = None
        ticks_per_qn = max(1, division)

    # ---- 收集所有轨道事件
    events: list[_Merged] = []
    pos = 8 + hlen
    found = 0
    while pos + 8 <= len(data) and found < max(1, ntrks):
        cid = data[pos:pos + 4]
        clen = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        body = pos + 8
        if cid != b"MTrk":
            pos = body + clen
            continue
        _parse_track(data, body, min(body + clen, len(data)), found, events)
        found += 1
        pos = body + clen

    if not events:
        raise MidiError("没有任何 MIDI 事件")

    events.sort(key=_Merged.key)

    # ---- 走时间轴，配对 note on/off
    midi = Midi(division=division if ticks_per_qn else 0)
    tempo = 500000
    first_tempo = 0
    tick_now = 0
    sec_now = 0.0
    programs = [0] * 16
    active: dict[tuple[int, int], tuple[float, int, int]] = {}
    last_note_end = 0.0

    def sec_per_tick() -> float:
        if ticks_per_second is not None:
            return 1.0 / ticks_per_second
        return tempo / 1_000_000.0 / ticks_per_qn

    for ev in events:
        if ev.tick != tick_now:
            sec_now += (ev.tick - tick_now) * sec_per_tick()
            tick_now = ev.tick

        k = ev.kind
        if k == "tempo":
            tempo = ev.a
            if not first_tempo:
                first_tempo = ev.a
                midi.tempo_us = ev.a
        elif k == "name" and not midi.name:
            midi.name = str(ev.a)
        elif k == "prog":
            programs[ev.a] = ev.b & 0x7F
        elif k == "on":
            key = (ev.a, ev.b)
            prev = active.get(key)
            if prev is not None:                    # 同音重复按新音处理
                start, vel, prog = prev
                midi.notes.append(Note(start, max(0.02, sec_now - start),
                                       ev.b, vel, prog, ev.a))
            active[key] = (sec_now, ev.c, 0 if ev.a == 9 else programs[ev.a])
        elif k == "off":
            key = (ev.a, ev.b)
            prev = active.pop(key, None)
            if prev is not None:
                start, vel, prog = prev
                dur = max(0.03, sec_now - start)
                midi.notes.append(Note(start, dur, ev.b, vel, prog, ev.a))
                last_note_end = max(last_note_end, start + dur)
        elif k == "alloff":
            ch = ev.a
            for key in [x for x in active if x[0] == ch]:
                start, vel, prog = active.pop(key)
                dur = max(0.03, sec_now - start)
                midi.notes.append(Note(start, dur, key[1], vel, prog, ch))
                last_note_end = max(last_note_end, start + dur)

    # 文件结束时还没关的音符，给一个短尾巴
    for (ch, pitch), (start, vel, prog) in active.items():
        dur = max(0.05, sec_now - start + 0.12)
        midi.notes.append(Note(start, dur, pitch, vel, prog, ch))
        last_note_end = max(last_note_end, start + dur)

    if not midi.notes:
        raise MidiError("解析出 0 个音符")

    midi.notes.sort(key=lambda n: n.start)
    midi.duration = max(last_note_end, max(n.start + n.dur for n in midi.notes), 0.05)
    return midi


# ---------------------------------------------------------------- iMelody
# MTK 平台的老铃声常用 IMY（iMelody 纯文本），结构上等价于单声部旋律。
# 语法：c4/d#5/r（休止）、v±（音量）、b（休止符长度）等，这里做轻量解析。
_IMY_NOTE = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def parse_imy(data: bytes) -> Midi:
    """解析 iMelody 文本（IMY）。"""
    try:
        text = data.decode("ascii", "ignore")
    except Exception as exc:                     # pragma: no cover
        raise MidiError(f"IMY 解码失败：{exc}") from exc

    if "BEGIN:IMELODY" not in text.upper():
        raise MidiError("不是 IMELODY")

    beat = 120.0
    name = ""
    melody = ""
    for line in text.splitlines():
        u = line.upper()
        if u.startswith("BEAT:"):
            try:
                beat = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif u.startswith("NAME:"):
            name = line.split(":", 1)[1].strip()
        elif "MELODY:" in u:
            melody = line.split(":", 1)[1].strip()
    if not melody:
        raise MidiError("IMY 没有 MELODY")

    # iMelody：默认时值 = 1/4 拍；'&' 延长上一个音，'r' 休止，'#'/'b' 升降
    beat_dur = 60.0 / max(20.0, beat)            # 一拍秒数
    default_len = beat_dur / 2.0                 # 默认 1/8 音符
    notes: list[Note] = []
    t = 0.0
    i = 0
    n = len(melody)
    while i < n:
        ch = melody[i]
        if ch in " \t,|":
            i += 1
            continue
        low = ch.lower()
        if low == "r":                            # 休止
            i += 1
            length = default_len
            if i < n and melody[i].isdigit():
                digits = ""
                while i < n and melody[i].isdigit():
                    digits += melody[i]
                    i += 1
                if digits:
                    length *= int(digits)
            t += length
            continue
        if low in _IMY_NOTE or low == "p":        # p = 休止（部分实现）
            semi = _IMY_NOTE.get(low, 0)
            i += 1
            if low == "p":
                t += default_len
                continue
            # 升降号
            while i < n and melody[i] in "#b":
                semi += 1 if melody[i] == "#" else -1
                i += 1
            # 八度
            octave = 1
            if i < n and melody[i] == "*":
                i += 1
                octave = 0
                while i < n and melody[i] == "*":
                    octave += 1
                    i += 1
            elif i < n and melody[i].isdigit():
                octave = int(melody[i])
                i += 1
            # 时值倍数
            mult = 1
            if i < n and melody[i].isdigit():
                digits = ""
                while i < n and melody[i].isdigit():
                    digits += melody[i]
                    i += 1
                if digits:
                    mult = int(digits)
            # 附点 / 双附点
            dotted = 1.0
            if i < n and melody[i] == ".":
                dotted = 1.5
                i += 1
                if i < n and melody[i] == ".":
                    dotted = 1.75
                    i += 1
            # & 连音：合并到上一个音符
            length = default_len * mult * dotted
            # MIDI 音高：C4 = 60 → octave 4 时 base
            pitch = 12 * (octave + 1) + semi
            pitch = max(0, min(127, pitch))
            if notes and i < n and melody[i] == "&":
                notes[-1].dur += length
                i += 1
            else:
                notes.append(Note(t, length, pitch, 100, 0, 0))
            t += length
            continue
        i += 1                                    # 未知字符跳过

    if not notes:
        raise MidiError("IMY 解析出 0 个音符")
    midi = Midi(notes=notes, duration=t, name=name, tempo_us=int(60_000_000 / max(20.0, beat)))
    return midi


def load(data: bytes) -> Midi:
    """按内容自动识别 SMF / IMY，统一返回 Midi。"""
    if not data:
        raise MidiError("空数据")
    head = data[:4]
    if head == b"MThd":
        return parse(data)
    if head in (b"RIFF",):
        raise MidiError("这是 RIFF/WAVE，不是 MIDI")
    if data.lstrip()[:5].upper().startswith(b"BEGIN"):
        return parse_imy(data)
    # 有些包把 mid 前面带了几个字节的私有头，找一下 MThd
    idx = data.find(b"MThd", 0, 256)
    if idx > 0:
        return parse(data[idx:])
    raise MidiError(f"无法识别的音频头：{data[:8]!r}")
