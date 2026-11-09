# mr_platEx(213x) - 获取当前的播放进度时间

```c
int32 mr_platEx (int32 code = 213x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取当前的播放进度时间。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | T_MEDIA_TIME数据结构指针 |
| output_len | T_MEDIA_TIME数据结构大小（字节数） |
| cb | 无 |

## 返回值

MR_SUCCESS 成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 备注

typedef struct
{
int32
pos;//pos：当前的播放进度时间，单位s。
}T_MEDIA_TIME;
platEx(213x),其中x代表音频类型的枚举值：
typedef
enum tagT_MEDIA_TYPE
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
T_MEDIA_TIME *time = NULL;
int32 len = 0;
mrc_platEx( 2133, NULL, 0,
(uint8**)&amp;time, (int32*)&amp;len, NULL );
mrc_printf( "Media total
time: %d.", time-&gt;pos );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
