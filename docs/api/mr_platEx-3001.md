# mr_platEx(3001) - 获取图片信息

```c
int32 mr_platEx (int32 code = 3001, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取图片信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | MRAPP_IMAGE_ORIGIN_T数据结构指针 |
| input_len | MRAPP_IMAGE_ORIGIN_T数据结构大小 |
| output | IMAGE_INFO数据结构指针地址 |
| output_len | IMAGE_INFO数据结构大小（字节数） |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 备注

输入数据结构：
typedef struct
{
char
*src;
//当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径
int32
len; //当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0
int32 src_type; //
枚举MRAPP_SRC_TYPE
} MRAPP_IMAGE_ORIGIN_T;
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
width; //图片的宽度
int32
height;
//图片的高度
}IMAGE_INFO;

## 示例

```c
/*mrp code*/
#define GIF_ANIMATION
"OATfile\\pic_test\\shoes.gif"
MRAPP_IMAGE_ORIGIN_T image_origin =
{0};
IMAGE_INFO *imageinfo = NULL;
int32
leninfo;
image_origin.src = (char
*)imagebuffer;
//图片数据流buffer
image_origin.len =
mrc_getLen(GIF_ANIMATION);
//图片大小
image_origin.src_type = SRC_STREAM;
mrc_platEx( 3001, (uint8* )&amp;image_origin, sizeof(image_origin),
(uint8**)&amp;imageinfo, (int32*)&amp;leninfo, NULL );
mrc_printf( "get
info: width=%d,height=%d", imageinfo-&gt;width, imageinfo-&gt;height
);
```

## 相关

Copyright ?2005-20010 SKY-MOBI
