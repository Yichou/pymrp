# mr_platEx(202x) - 加载一个文件

```c
int32 mr_platEx (int32 code = 202x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

加载一个文件。

## 参数

| 参数 | 说明 |
|---|---|
| input | 文件名指针，文件名可以带路径 |
| input_len | 文件名长度 |
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

platEx(202x),其中x代表音频类型的枚举值：
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
mrc_platEx( 2024, (uint8*)"testsound_amr.amr", strlen(
"testsound_amr.amr",), NULL, NULL, 0 );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
