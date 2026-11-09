# mr_platEx(2700) - 开始录音

```c
int32 mr_platEx (int32 code = 2700, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

开始录音。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_DSM_VOICE_REC_REQ数据结构指针 |
| input_len | T_DSM_VOICE_REC_REQ 数据结构大小 |
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

数据结构如下：
typedef struct
{
char
*src;
/*录音文件的相对文件名*/
int32
src_len;
int32 src_type;
int32 format; /* MR_SOUND_WAV ,
MR_SOUND_PCM , MR_SOUND_AMR ,
MR_SOUND_AMR_WB
*/
}T_DSM_VOICE_REC_REQ;
注：录音的异常情况通过mr_event通知，mr_event的参数如下：
第一个：MR_ERROR_EVENT
第二个：DSM_ERROR_NO_SPACE：空间满
MED_RES_TERMINATED：被中断
DSM_ERROR_UNKNOW：未知错误
第三个：0

## 示例

```c
/*mrp code*/
#define NAME "OATfile\\record_test\\rec_get_pcmdata.pcm"
#define
REC_LEN 10*1024;
T_DSM_VOICE_REC_REQ recReq = { 0
};
recReq.src = NAME ;
recReq.format = MR_SOUND_WAV
;
recReq.src_len = REC_LEN;
recReq.src_type =
SRC_STREAM;
mrc_platEx( 2700, (uint8*)&amp;recReq, sizeof(
T_DSM_VOICE_REC_REQ ), NULL, NULL, 0 );
```

## 相关

mr_plat(2703)
Copyright ?2005-20010 SKY-MOBI
