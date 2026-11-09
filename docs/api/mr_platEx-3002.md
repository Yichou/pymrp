# mr_platEx(3002) - 图片解码

```c
int32 mr_platEx (int32 code = 3002, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

解码一张图片，将解完的数据放到dest所指的buf中，并通知vm解码结果。（gif不在此中处理）。

## 参数

| 参数 | 说明 |
|---|---|
| input | MRAPP_IMAGE_DECODE_T数据结构指针 |
| input_len | MRAPP_IMAGE_DECODE_T数据结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED 失败
MR_WAITING
异步模式，需要使用命令轮询以获取状态
MR_IGNORE
不支持该功能
(注1：特殊平台可能有特殊返回值处理，当前不做考虑)

## 备注

输入数据结构：
typedef struct
{
char
*src;
//当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径
int32
len; //当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0
int32 width;
//图片宽度
int32
height; //图片高度
int32 src_type; //
枚举MRAPP_SRC_TYPE
char
*dest;
//rgb565 bmp格式(注1)
} MRAPP_IMAGE_DECODE_T;
typedef
enum
{
SRC_NAME =
0,
//传到移植接口的是文件名
SRC_STREAM
//传到移植接口的是图片数据流
}MRAPP_SRC_TYPE;

## 示例

```c
/*mrp code*/
#define PNG_IMAGE "OATfile\\pic_test\\image.png"
U8
imagebuffer[100*100];
MRAPP_IMAGE_DECODE_T decodeReq = {0};
memset(
imagebuffer, 0, sizeof(imagebuffer) );
decodeReq.src = (char
*)PNG_IMAGE;
decodeReq.src_type = SRC_NAME;
decodeReq.width =
24;
decodeReq.height = 24;
decodeReq.dest = (char*)imagebuffer;
mrc_platEx( 3002, (uint8* )&amp;decodeReq, sizeof(MRAPP_IMAGE_DECODE_T),
NULL, NULL, NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
