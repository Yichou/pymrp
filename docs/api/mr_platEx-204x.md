# mr_platEx(204x) - 从当前的位置开始播放

```c
int32 mr_platEx (int32 code = 204x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

从当前的位置开始播放。

## 参数

| 参数 | 说明 |
|---|---|
| input | Block：1，阻塞播放；0，不阻塞播放 |
| input_len | 0 或 &gt;=12 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

当input_len为0时不需要使用回调函数，当input_len&gt;=12时，input传入一个结构，结构定义如下：
input：struct指针
input_len：struct长度
struct：
typedef
struct
{
ACI_PLAY_CB cb; //回调函数
int32 loop;
int32
block;
};
typedef void (*ACI_PLAY_CB)(int32
result);
回调有两种可能的返回值：
ACI_PLAY_COMPLETE 0
//播放结束
ACI_PLAY_ERROR 1
//播放时遇到错误
Loop
：1，循环播放；0，不循环播放；2，PCM循环播放模式

## 返回值

MR_SUCCESS 成功
MR_FAILED 失败
MR_WAITING
异步模式，需要使用ACI_STATUS命令轮询以获取状态
MR_IGNORE 不支持该功能

## 备注

platEx(204x),其中x代表音频类型的枚举值：
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
mrc_platEx( 2044, NULL, 0, NULL, NULL, NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
