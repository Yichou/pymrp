# mr_platEx(225x) - 多通道释放已经加载的数据

```c
int32 mr_platEx (int32 code = 225x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

释放已经加载的数据。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向句柄的值 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS 成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 备注

platEx(225x),其中x代表音频类型的枚举值：
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
mrc_platEx( 2252, (uint8*)&amp;hdl_wav, sizeof(int32), NULL, NULL,
NULL); //hdl_wav 为platEx（222x）得到的句柄
```

## 相关

mr_platEx(222x)
Copyright ?2005-20010 SKY-MOBI
