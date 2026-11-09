# mr_platEx(210x) - 设置播放位置，已经播放了多少时间

```c
int32 mr_platEx (int32 code = 210x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置播放位置，已经播放了多少时间。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_SET_PLAY_POS数据结构指针 |
| input_len | T_SET_PLAY_POS数据结构长度 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS 成功
MR_FAILED 失败
MR_WAITING
异步模式，需要使用ACI_STATUS命令轮询以获取状态
MR_IGNORE 不支持该功能

## 备注

typedef struct
{
int32 pos;
//单位,秒s.
}T_SET_PLAY_POS;
platEx(210x),其中x代表音频类型的枚举值：
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

## 示例

```c
/*mrp code*/
T_SET_PLAY_POS setPos = { 0 }；
setPos.pos = 18;
mrc_platEx( codes,
(uint8*)&amp;setPos, sizeof(setPos), NULL, NULL, NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
