# mr_playSound

```c
int32 mr_playSound(int type, const void* data, uint32 dataLen, int32 loop)
```

## 说明

播放音频。

## 参数

| 参数 | 说明 |
|---|---|
| type | //8K |
| data | 音频数据 |
| datalen | 数据长度 |
| loop | !=0，音乐循环播放；==0，单次播放 |

音频类型，取值可以为：
MR_SOUND_MIDI,
MR_SOUND_WAV,
MR_SOUND_MP3,
MR_SOUND_AMR,
MR_SOUND_PCM

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

调用mr_playSound播放音频，调用mr_stopSound停止播放音频。

## 示例

```c
/*mrp code*/
VOID* data; // 音频数据流地址
int32
len; //数据长度
mr_playSoundEx( MR_SOUND_MIDI, data, len, 0
);
```

## 相关

mr_stopSound
Copyright ?2005-20010 SKY-MOBI
