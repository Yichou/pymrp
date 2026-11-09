# mr_platEx(209x) - 获取当前设备的状态

```c
int32 mr_platEx (int32 code = 209x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取当前设备的状态。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_PLAT_VALUE_BASE + 设备状态值
成功
MR_FAILED 失败
MR_WAITING
异步模式，需要使用ACI_STATUS命令轮询以获取状态
MR_IGNORE
不支持该功能
返回成功得到状态，其枚举值为:
typedef enum
tag_PLAY_STATE
{
MR_MEDIA_IDLE= 1001, /*1.not init;
2.device closed*/
MR_MEDIA_INITED = 1002,
MR_MEDIA_LOADED = 1003, /*1.loaded not play; 2.play finished;
3.play stoped*/
MR_MEDIA_PLAYING =
1004,/*1.playing*/
MR_MEDIA_PAUSED =
1005, /*1.paused*/
MR_MEDIA_SUSPENDED = 1006,
MR_MEDIA_SUSPENDING = 1007
}PLAY_STATE;

## 备注

platEx(209x),其中x代表音频类型的枚举值：
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
int32 devState = 0;
devState = mrc_platEx( 2094, NULL, 0, NULL, NULL, 0
);
```

## 相关

Copyright ?2005-20010 SKY-MOBI
