"""音频子系统。

MRP 的声音只有两个入口，但背后的格式五花八门：

    midi.py   SMF(iMelody 也算) 解析  —— mr_playSound(MR_SOUND_MIDI)
    wav.py    RIFF/WAVE 解析 + 重采样 —— mr_playSound(MR_SOUND_WAV)
    synth.py  numpy 波表合成          —— 把 Midi 变成 PCM
    stream.py 分段 PCM 流无缝拼接      —— mr_playSound(MR_SOUND_PCM) 连续调用
    mixer.py  pygame.mixer 门面        —— 统一 play/stop/缓存/统计
"""

from .mixer import AudioEngine

__all__ = ["AudioEngine"]
