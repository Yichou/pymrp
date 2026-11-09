# mr_stopSound

```c
int32 mr_stopSound (int type)
```

## 说明

停止播放音频。

## 参数

| 参数 | 说明 |
|---|---|
| type | //8K |

音频类型，取值可以为：
MR_SOUND_MIDI,
MR_SOUND_WAV,
MR_SOUND_MP3,
MR_SOUND_PCM

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

调用mr_playSound播放音频，调用mr_stopSound停止播放音频。

## 示例

```c
/*mrp code*/
mr_stopSoundEx( MR_SOUND_MIDI
);
```

## 相关

mr_playSound
Copyright ?2005-20010 SKY-MOBI
