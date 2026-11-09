# mr_platEx(222x) - 多通道加载

```c
int32 mr_platEx (int32 code = 222x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

多通道加载。加载一个用于多通道的数据，目前只支持wav和midi 。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_BG_PLAY_REQ数据结构指针 |
| input_len | T_BG_PLAY_REQ数据结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_FAILED
失败
其他
一个句柄，以后操作（播放，停止，关闭）都使用本句柄。

## 备注

typedef struct
{
uint8
*data;
uint32 len;
int32
loop;
}T_BG_PLAY_REQ;
platEx(222x),其中x代表音频类型的枚举值：
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
void GetAudioDataStream(const char* name,char*buf,int32
buflen)
{
MR_FILE_HANDLE fh;
int
len=0;
fh = mrc_open( name, MR_FILE_RDONLY );
len = mrc_read( fh, (void *)buf, buflen );
mrc_close(
fh) ;
}
int32 MultipathLoadAudio(const char*
audioName)
{
T_BG_PLAY_REQ loadReq;
int32
len_wav;
char *buffer_wav = NULL;
int32
hdl_wav = 0;
len_wav = mrc_getLen( audioName
);
buffer_wav = (char*)malloc(len_wav);
GetAudioDataStream( audioName, buffer_wav, len_wav );
loadReq.data = buffer_wav;
loadReq.len =
len_wav;
loadReq.loop = 0;
hdl_wav =
mrc_platEx( 2222, (uint8*)&amp;loadReq, sizeof(T_BG_PLAY_REQ), NULL, NULL,
NULL );
if(MR_FAILED == re)
return MR_FAILED;
else
return hdl_wav;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
