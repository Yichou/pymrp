# mr_platEx(221x) - 释放IRAM

```c
int32 mr_platEx (int32 code = 221x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

释放IRAM。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE
不支持该功能

## 备注

platEx(221x),其中x代表音频类型的枚举值：
typedef enum
tagT_MEDIA_TYPE
{
MEDIA_MIDI = 1,
MEDIA_WAVE,
MEDIA_MP3,
MEDIA_AMR,
MEDIA_PCM,
MEDIA_M4A,
MEDIA_AAC,
MEDIA_LYRIC,
MEDIA_UNKNOW
}T_MEDIA_TYPE;

## 相关

Copyright ?2005-20010 SKY-MOBI
