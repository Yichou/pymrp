"""mr_platEx 的多媒体播放器 —— MRP 的第二条声音通路（流媒体播放）。

和 ``mr_playSound`` 一次给全量数据不同，这是一台**有状态播放器**，按音频
类型各开一路（``x`` = T_MEDIA_TYPE）：

    201x 设备初始化       202x 加载文件        203x 加载内存缓冲
    204x 播放(loop/block) 205x 暂停            206x 继续
    207x 停止             208x 关闭设备        209x 查状态
    210x 定位(秒)         211x 定位(字节偏移)  212x 总时长
    213x/215x 当前进度    216x 释放
    222x 多通道加载       223x 播放  224x 停止  225x 释放

典型用法就是「边读边播」：应用 mr_open/mr_read 把音频读进内存，再交给
播放器；播放器自己推进时间轴，应用通过 209x/213x 轮询状态和进度。

为什么不用 pygame.mixer.music：那是个全局单例，pause/resume/seek 会互相
打架，而且 MIDI 在 Windows 的 SDL2_mixer 上没有解码器。这里自己持有 PCM
数组 + 一个专用 Channel，seek 就是重新切片播放，行为可控且跨平台一致。
"""

from __future__ import annotations

import time

import numpy as np

from ..consts import (
    MEDIA_AMR,
    MEDIA_AAC,
    MEDIA_LYRIC,
    MEDIA_M4A,
    MEDIA_MIDI,
    MEDIA_MP3,
    MEDIA_PCM,
    MEDIA_TYPE_NAMES,
    MEDIA_UNKNOW,
    MEDIA_WAVE,
    MR_FAILED,
    MR_IGNORE,
    MR_MEDIA_IDLE,
    MR_MEDIA_INITED,
    MR_MEDIA_LOADED,
    MR_MEDIA_PAUSED,
    MR_MEDIA_PLAYING,
    MR_PLAT_VALUE_BASE,
    MR_SUCCESS,
    PLATEX_MEDIA_BG_FREE,
    PLATEX_MEDIA_BG_LOAD,
    PLATEX_MEDIA_BG_PLAY,
    PLATEX_MEDIA_BG_STOP,
    PLATEX_MEDIA_CLOSE,
    PLATEX_MEDIA_CUR_TIME,
    PLATEX_MEDIA_CUR_TIME2,
    PLATEX_MEDIA_INIT,
    PLATEX_MEDIA_LOAD_BUF,
    PLATEX_MEDIA_LOAD_FILE,
    PLATEX_MEDIA_PAUSE,
    PLATEX_MEDIA_PLAY,
    PLATEX_MEDIA_RELEASE,
    PLATEX_MEDIA_RESUME,
    PLATEX_MEDIA_SEEK_OFFSET,
    PLATEX_MEDIA_SEEK_TIME,
    PLATEX_MEDIA_STATE,
    PLATEX_MEDIA_STOP,
    PLATEX_MEDIA_TOTAL_TIME,
)
from . import midi as midi_mod
from . import synth
from . import wav as wav_mod

# 支持解码的类型：MIDI / WAVE / PCM。其余（MP3/M4A/AAC/AMR）需要完整解码器，
# 不在模拟范围内，明确返回 MR_IGNORE 让应用自己降级。
_DECODABLE = {MEDIA_MIDI, MEDIA_WAVE, MEDIA_PCM}


def decode_audio(engine, mtype: int, data: bytes) -> tuple[np.ndarray, str]:
    """把一段音频字节解码成引擎采样率的 float32 单声道 PCM。"""
    sr = engine.sample_rate
    if not data:
        raise ValueError("空数据")

    if mtype == MEDIA_MIDI:
        song = midi_mod.load(data)
        buf = synth.render(song, sr)
        # render 会在末尾留保护尾巴，裁掉它，让 duration 等于音乐本身的长度
        keep = min(len(buf), int(song.duration * sr) + int(0.02 * sr))
        return buf[:keep], song.summary()

    if mtype == MEDIA_WAVE:
        w = wav_mod.parse(data)
        arr = w.samples if w.rate == sr else wav_mod.resample(w.samples, w.rate, sr)
        return arr, w.summary()

    if mtype == MEDIA_PCM:
        # MR_SOUND_PCM //8K：8kHz 16bit 单声道裸数据
        n = len(data) // 2 * 2
        arr = np.frombuffer(data[:n], dtype="<i2").astype(np.float32) / 32768.0
        if engine.pcm_rate != sr:
            arr = wav_mod.resample(arr, engine.pcm_rate, sr)
        return arr, f"PCM {len(data)}B @{engine.pcm_rate}Hz"

    raise ValueError(f"{MEDIA_TYPE_NAMES.get(mtype, mtype)} 解码器不在模拟范围内")


class MediaPlayer:
    """一路流媒体播放器（对应一个 T_MEDIA_TYPE）。"""

    def __init__(self, engine, mtype: int) -> None:
        self.engine = engine
        self.mtype = mtype
        self.name = MEDIA_TYPE_NAMES.get(mtype, f"type{mtype}")
        self.state = MR_MEDIA_IDLE
        self.pcm: np.ndarray | None = None
        self.loop = 0
        self.source = ""
        self.desc = ""

        self._ch = None
        self._hold = None
        self._offset = 0.0          # 本轮播放的起点（秒）
        self._t0 = 0.0              # 起点对应的 monotonic
        self._frozen = 0.0          # 暂停时冻结的进度

    # ------------------------------------------------------------ 基本信息
    @property
    def duration(self) -> float:
        if self.pcm is None:
            return 0.0
        return len(self.pcm) / float(self.engine.sample_rate)

    def position(self) -> float:
        d = self.duration
        if self.state == MR_MEDIA_PAUSED:
            return min(self._frozen, d)
        if self.state != MR_MEDIA_PLAYING:
            return min(self._offset, d)
        elapsed = self._offset + (time.monotonic() - self._t0)
        if self.loop and d > 0:
            return elapsed % d
        return min(elapsed, d)

    def _log(self, msg: str) -> None:
        if self.engine.log:
            self.engine.log(f"[media:{self.name}] {msg}")

    # ------------------------------------------------------------ 设备
    def init(self) -> int:
        if self.state == MR_MEDIA_IDLE:
            self.state = MR_MEDIA_INITED
        return MR_SUCCESS

    def close(self) -> int:
        self._halt()
        self.state = MR_MEDIA_IDLE
        self._log("设备关闭")
        return MR_SUCCESS

    # ------------------------------------------------------------ 加载
    def load_bytes(self, data: bytes, source: str) -> int:
        if self.mtype not in _DECODABLE:
            self._log(f"{self.name} 不支持解码，返回 MR_IGNORE")
            return MR_IGNORE
        try:
            pcm, desc = decode_audio(self.engine, self.mtype, data)
        except Exception as exc:
            self._log(f"加载失败：{type(exc).__name__}: {exc}")
            return MR_FAILED

        self._halt()
        self.pcm = np.ascontiguousarray(pcm, dtype=np.float32)
        self.desc = desc
        self.source = source
        self._offset = 0.0
        self._frozen = 0.0
        self.state = MR_MEDIA_LOADED
        self._log(f"加载 {source} → {desc} 共 {self.duration:.2f}s")
        return MR_SUCCESS

    def load_file(self, name: str, fs) -> int:
        try:
            data = fs.read_all(name)
        except Exception as exc:
            self._log(f"读文件失败 {name}: {exc}")
            return MR_FAILED
        return self.load_bytes(data, name)

    # ------------------------------------------------------------ 播放控制
    def _channel(self):
        if self.engine.ok:
            return self.engine.media_channel_obj()
        return None

    def _halt(self) -> None:
        if self._ch is not None:
            self._ch.stop()
        self._hold = None

    def _start(self, sec: float) -> None:
        """从 sec 秒处起播（seek 也走这里，重新切片）。"""
        self._halt()
        if self.pcm is None:
            return
        sr = self.engine.sample_rate
        start = max(0, min(int(sec * sr), max(0, self.pcm.size - 1)))
        clip = self.pcm[start:]
        self._offset = start / float(sr)

        if not self.engine.ok:
            self._t0 = time.monotonic()
            self.state = MR_MEDIA_PLAYING
            return

        import pygame
        pcm = synth.to_stereo16(clip, self.engine.channels)
        try:
            sound = pygame.mixer.Sound(buffer=pcm)
        except Exception as exc:
            self._log(f"创建 Sound 失败：{exc}")
            self.state = MR_MEDIA_LOADED
            return
        sound.set_volume(self.engine.volume)
        ch = self._channel()
        ch.play(sound, loops=-1 if self.loop else 0)
        self._ch = ch
        self._hold = sound
        self._t0 = time.monotonic()
        self.state = MR_MEDIA_PLAYING

    def play(self, loop: int = 0) -> int:
        if self.pcm is None:
            self._log("没有加载数据，无法播放")
            return MR_FAILED
        self.loop = 1 if loop else 0
        # 204x 的语义是"从当前的位置开始播放"
        resume_at = self._frozen if self.state == MR_MEDIA_PAUSED else self._offset
        self._start(resume_at)
        self._log(f"播放（{self._offset:.2f}s 起{'，循环' if self.loop else ''}）")
        return MR_SUCCESS if self.state == MR_MEDIA_PLAYING else MR_FAILED

    def pause(self) -> int:
        if self.state != MR_MEDIA_PLAYING:
            return MR_FAILED
        self._frozen = self.position()
        if self._ch is not None:
            self._ch.pause()
        self.state = MR_MEDIA_PAUSED
        self._log(f"暂停 @{self._frozen:.2f}s")
        return MR_SUCCESS

    def resume(self) -> int:
        if self.state != MR_MEDIA_PAUSED:
            return MR_FAILED
        self._offset = self._frozen
        self._t0 = time.monotonic()
        if self._ch is not None:
            self._ch.unpause()
        self.state = MR_MEDIA_PLAYING
        self._log(f"继续 @{self._frozen:.2f}s")
        return MR_SUCCESS

    def stop(self) -> int:
        self._halt()
        self._offset = 0.0
        self._frozen = 0.0
        self.state = MR_MEDIA_LOADED if self.pcm is not None else MR_MEDIA_INITED
        self._log("停止")
        return MR_SUCCESS

    def release(self) -> int:
        self._halt()
        self.pcm = None
        self._offset = 0.0
        self._frozen = 0.0
        self.state = MR_MEDIA_IDLE
        self._log("释放")
        return MR_SUCCESS

    # ------------------------------------------------------------ 定位
    def seek_seconds(self, sec: float) -> int:
        if self.pcm is None:
            return MR_FAILED
        sec = max(0.0, min(float(sec), max(0.0, self.duration - 0.01)))
        self._offset = sec
        self._frozen = sec
        if self.state == MR_MEDIA_PLAYING:
            self._start(sec)
        self._log(f"定位到 {sec:.2f}s")
        return MR_SUCCESS

    def seek_bytes(self, offset: int) -> int:
        """按字节偏移定位。裸 PCM 下就是 offset/(2*rate) 秒。"""
        if self.mtype == MEDIA_PCM:
            sec = offset / float(max(1, self.engine.pcm_rate) * 2)
        else:
            sec = offset / float(max(1, self.engine.sample_rate) * 2)
        return self.seek_seconds(sec)

    # ------------------------------------------------------------ 状态
    def state_code(self) -> int:
        """209x 的返回：MR_PLAT_VALUE_BASE + PLAY_STATE。"""
        return MR_PLAT_VALUE_BASE + self.state

    def tick(self) -> None:
        """每帧推进：自然播完 → 回到 LOADED。"""
        if self.state != MR_MEDIA_PLAYING or self.loop:
            return
        if self.pcm is None:
            return
        if self._ch is not None and not self._ch.get_busy():
            self.state = MR_MEDIA_LOADED
            self._offset = 0.0
            self._log("播放结束")


class MediaRack:
    """按音频类型管理多路播放器 + 多通道背景音。"""

    def __init__(self, engine) -> None:
        self.engine = engine
        self.players: dict[int, MediaPlayer] = {}
        self._bg: dict[int, dict] = {}
        self._next_handle = 1
        self.calls = 0

    # ------------------------------------------------------------ 路由
    def player(self, mtype: int) -> MediaPlayer:
        p = self.players.get(mtype)
        if p is None:
            p = MediaPlayer(self.engine, mtype)
            self.players[mtype] = p
        return p

    def tick(self) -> None:
        for p in self.players.values():
            p.tick()

    def release_all(self) -> None:
        """释放所有播放器与背景音（应用退出 / 崩溃收尾时用）。"""
        for p in list(self.players.values()):
            try:
                p.release()
            except Exception:
                pass
        self.players.clear()
        self._bg.clear()

    def stats(self) -> str:
        if not self.players:
            return "流媒体: 未使用"
        from ..consts import MEDIA_STATE_NAMES
        bits = []
        for mt in sorted(self.players):
            p = self.players[mt]
            if p.state == MR_MEDIA_IDLE and p.pcm is None:
                continue
            state = MEDIA_STATE_NAMES.get(p.state, str(p.state))
            bits.append(f"{p.name}={state}({p.duration:.1f}s)")
        if not bits:
            return "流媒体: 未使用"
        return "流媒体 " + " ".join(bits)

    # ------------------------------------------------------------ 分发
    def handle(self, code: int, mem, input_addr: int, input_len: int,
               output_ptr: int, output_len_ptr: int, fs) -> int | None:
        """处理 201x..225x。不是这类编号就返回 None，让调用方走别的分支。"""
        family, mtype = divmod(code, 10)

        # ---- 多通道（222x-225x）：不同签名，先处理
        if family in (PLATEX_MEDIA_BG_LOAD, PLATEX_MEDIA_BG_PLAY,
                      PLATEX_MEDIA_BG_STOP, PLATEX_MEDIA_BG_FREE):
            return self._handle_bg(family, mem, input_addr, input_len)

        if family < PLATEX_MEDIA_INIT or family > PLATEX_MEDIA_RELEASE:
            return None
        if mtype < MEDIA_MIDI or mtype > MEDIA_UNKNOW:
            return None

        self.calls += 1
        p = self.player(mtype)

        if family == PLATEX_MEDIA_INIT:
            return p.init()
        if family == PLATEX_MEDIA_LOAD_FILE:
            name = mem.cstr(input_addr, 260) if input_addr else ""
            return p.load_file(name, fs) if name else MR_FAILED
        if family == PLATEX_MEDIA_LOAD_BUF:
            # LOAD_AUDIO_DATA_REQ { char *buf; int32 buf_len; }
            if not input_addr or input_len < 8:
                # 有些实现直接把裸数据塞进来，没有包装结构
                return p.load_bytes(mem.read(input_addr, input_len)
                                    if input_addr and input_len else b"", "<buffer>")
            buf_ptr = mem.u32(input_addr)
            buf_len = mem.s32(input_addr + 4)
            if not mem.valid(buf_ptr, 1) or buf_len <= 0:
                return MR_FAILED
            buf_len = min(buf_len, mem.base + mem.size - buf_ptr)
            return p.load_bytes(mem.read(buf_ptr, buf_len), "<buffer>")
        if family == PLATEX_MEDIA_PLAY:
            loop = 0
            if input_addr and input_len >= 12:
                # struct { ACI_PLAY_CB cb; int32 loop; int32 block; }
                loop = mem.s32(input_addr + 4)
            return p.play(loop)
        if family == PLATEX_MEDIA_PAUSE:
            return p.pause()
        if family == PLATEX_MEDIA_RESUME:
            return p.resume()
        if family == PLATEX_MEDIA_STOP:
            return p.stop()
        if family == PLATEX_MEDIA_CLOSE:
            return p.close()
        if family == PLATEX_MEDIA_STATE:
            return p.state_code()
        if family == PLATEX_MEDIA_SEEK_TIME:
            # T_SET_PLAY_POS { int32 pos; }  单位：秒
            pos = mem.s32(input_addr) if input_addr else 0
            return p.seek_seconds(pos)
        if family == PLATEX_MEDIA_SEEK_OFFSET:
            off = mem.s32(input_addr) if input_addr else 0
            return p.seek_bytes(off)
        if family == PLATEX_MEDIA_TOTAL_TIME:
            return self._write_time(mem, output_ptr, output_len_ptr,
                                    int(p.duration), p)
        if family in (PLATEX_MEDIA_CUR_TIME, PLATEX_MEDIA_CUR_TIME2):
            return self._write_time(mem, output_ptr, output_len_ptr,
                                    int(p.position()), p)
        if family == PLATEX_MEDIA_RELEASE:
            return p.release()
        return MR_IGNORE

    # ------------------------------------------------------------ 工具
    def _write_time(self, mem, output_ptr: int, output_len_ptr: int,
                    seconds: int, p: MediaPlayer) -> int:
        """T_MEDIA_TIME { int32 pos; } —— 宿主分配，把指针写回 *output。"""
        if not output_ptr or not mem.valid(output_ptr, 4):
            return MR_FAILED
        addr = mem.malloc(8)
        if addr is None:
            return MR_FAILED
        mem.set_u32(addr, seconds & 0xFFFFFFFF)
        mem.set_u32(output_ptr, addr)
        if output_len_ptr and mem.valid(output_len_ptr, 4):
            mem.set_u32(output_len_ptr, 4)
        return MR_SUCCESS

    # ------------------------------------------------------------ 多通道
    def _handle_bg(self, family: int, mem, input_addr: int, input_len: int) -> int:
        if family == PLATEX_MEDIA_BG_LOAD:
            # T_BG_PLAY_REQ { uint8 *data; uint32 len; int32 loop; }
            if not input_addr or input_len < 12:
                return MR_FAILED
            data_ptr = mem.u32(input_addr)
            data_len = mem.u32(input_addr + 4)
            loop = mem.s32(input_addr + 8)
            if not mem.valid(data_ptr, 1) or data_len == 0:
                return MR_FAILED
            data_len = min(data_len, mem.base + mem.size - data_ptr)
            data = mem.read(data_ptr, min(data_len, 4 << 20))

            # 多通道只支持 wav / midi（手册明确说明）
            pcm = None
            for mt in (MEDIA_WAVE, MEDIA_MIDI):
                try:
                    pcm, desc = decode_audio(self.engine, mt, data)
                    break
                except Exception:
                    continue
            if pcm is None:
                if self.engine.log:
                    self.engine.log("[media:bg] 多通道只支持 WAV/MIDI，数据无法解码")
                return MR_FAILED

            handle = self._next_handle
            self._next_handle += 1
            self._bg[handle] = {"pcm": pcm, "loop": loop, "sound": None,
                                "ch": None, "desc": desc}
            if self.engine.log:
                self.engine.log(f"[media:bg] 加载句柄 {handle}: {desc}")
            return handle

        # 其余三个都靠句柄，input 指向句柄值本身
        if not input_addr or not mem.valid(input_addr, 4):
            return MR_FAILED
        handle = mem.s32(input_addr)
        item = self._bg.get(handle)
        if item is None:
            return MR_FAILED

        if family == PLATEX_MEDIA_BG_PLAY:
            if not self.engine.ok:
                return MR_SUCCESS
            import pygame
            pcm = synth.to_stereo16(item["pcm"], self.engine.channels)
            try:
                sound = pygame.mixer.Sound(buffer=pcm)
            except Exception:
                return MR_FAILED
            sound.set_volume(self.engine.volume)
            ch = pygame.mixer.Channel(self.engine.bg_channel_index(handle))
            ch.play(sound, loops=-1 if item["loop"] else 0)
            item["sound"] = sound
            item["ch"] = ch
            return MR_SUCCESS

        if family == PLATEX_MEDIA_BG_STOP:
            if item["ch"] is not None:
                item["ch"].stop()
            return MR_SUCCESS

        if family == PLATEX_MEDIA_BG_FREE:
            if item["ch"] is not None:
                item["ch"].stop()
            self._bg.pop(handle, None)
            return MR_SUCCESS

        return MR_IGNORE
