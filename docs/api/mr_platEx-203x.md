# mr_platEx(203x) - 加载缓冲数据

```c
int32 mr_platEx (int32 code = 203x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

加载缓冲数据。

## 参数

| 参数 | 说明 |
|---|---|
| input | LOAD_AUDIO_DATA_REQ数据结构指针 |
| input_len | LOAD_AUDIO_DATA_REQ数据结构长度 |
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
char* buf; //缓冲数据指针
int32
buf_len; //缓冲数据长度
}LOAD_AUDIO_DATA_REQ;
platEx(203x),其中x代表音频类型的枚举值：
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
#define audioBufLen 150*1024
void GetAudioDataStream(const char* name, char*buf, int32
buflen)
{
MR_FILE_HANDLE fh;
int len=0;
fh = mrc_open( name, MR_FILE_RDONLY);
len =
mrc_read( fh, (void *)buf, buflen );
mrc_close(fh);
}
void LoadBufferData(void)
{
char *buffer =
NULL;
LOAD_AUDIO_DATA_REQ loadReq;
buffer
= (char*)malloc( audioBufLen );
GetAudioDataStream(
"testsound_amr.amr", buffer, audioBufLen );
loadReq.buf =
buffer;
loadReq.buf_len = audioBufLen;
mrc_platEx( 2034, (uint8*)&amp;loadReq, sizeof(LOAD_AUDIO_DATA_REQ), NULL,
NULL, NULL );
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
