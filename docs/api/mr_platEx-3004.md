# mr_platEx(3004) - gif解码

```c
int32 mr_platEx (int32 code = 3004, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

解码一张GIF图片，将解完的数据放到dest所指的buf中，并通知vm解码结果。

## 参数

| 参数 | 说明 |
|---|---|
| input | MRAPP_IMAGE_DECODE_T数据结构指针 |
| input_len | MRAPP_IMAGE_DECODE_T数据结构大小 |
| output | MRAPP_GIF_HEADER数据结构指针地址 |
| output_len | MRAPP_GIF_HEADER数据结构大小 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE
不支持该功能

## 备注

输入数据结构：
typedef struct
{
char
*src;
//文件名或是数据流的buf的地址，如果是文件名，是GB格式
int32
len;
//src所指的buf的大小
int32
width;
//用于图片显示的区域的宽度
int32
height;
//用于图片显示的区域的高度
int32
src_type; //
枚举MRAPP_SRC_TYPE
char
*dest;
//解码后的图片数据存放的buffer
}MRAPP_IMAGE_DECODE_T;
typedef
enum
{
SRC_NAME =
0,
//传到移植接口的是文件名
SRC_STREAM
//传到移植接口的是图片数据流
}MRAPP_SRC_TYPE;
输出数据结构：
typedef struct
{
int32
id;
int32
width;
//gif的宽度
int32
height;
//gif的高度
int
bg_color; //gif的背景色
int
frame_count;
//gif总的帧数
MRAPP_GIF_FRAME_INFO_T
*first;
//指向gif的第一帧的数据结构
}MRAPP_GIF_HEADER;
typedef struct
_MRAPP_GIF_FRAME_INFO
{
int32
fwidth;
//本帧的宽度
int32
fheight;
//本帧的高度
int32
ox; //本帧左上角的x坐标(相对逻辑屏幕)
int32
oy;
//本帧左上角的y坐标(相对逻辑屏幕)
int32
transparent_flag;
//是否需要透明显示
int32
transparent_color; //透明显示的颜色
int32
delay_time;
//本帧显示的时间
char
*pdata;
//解压好的图片数据
struct _MRAPP_GIF_FRAME_INFO *next;
//指向下一帧的数据结构
}MRAPP_GIF_FRAME_INFO_T;

## 示例

```c
/*mrp code*/
#define GIF_IMAGE "OATfile\\pic_test\\image.gif"
U8
imagebuffer[100*100];
MRAPP_IMAGE_DECODE_T decodeReq =
{0};
MRAPP_GIF_HEADER *decodeRsp = NULL;
int32 len;
memset(
imagebuffer, 0, sizeof(imagebuffer) );
decodeReq.src = (char
*)GIF_IMAGE;
decodeReq.src_type = SRC_NAME;
decodeReq.width =
40;
decodeReq.height = 40;
decodeReq.dest = (char*)imagebuffer;
mrc_platEx( 3004, (uint8* )&amp;decodeReq, sizeof(MRAPP_IMAGE_DECODE_T),
(uint8**)&amp;decodeRsp, (int32*)&amp;len, NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
