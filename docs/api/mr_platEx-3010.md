# mr_platEx(3010) - 直接调用平台接口将图片绘制到指定的矩形内

```c
int32 mr_platEx (int32 code = 3010, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

直接调用平台接口将图片绘制到指定的矩形内。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_DRAW_DIRECT_REQ数据结构指针 |
| input_len | T_DRAW_DIRECT_REQ数据结构大小 |
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

输入数据结构：
typedef struct
{
char
*src; //当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径
int32
src_len;
//当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0
int32
src_type;
//枚举MRAPP_SRC_TYPE
int32
ox; //图片显示在x坐标
int32
oy;
//图片显示在y坐标
int32
w;
//图片宽度
int32
h;
//图片高度
}T_DRAW_DIRECT_REQ;
typedef enum
{
SRC_NAME = 0,
//传到移植接口的是文件名
SRC_STREAM
//传到移植接口的是图片数据流
}MRAPP_SRC_TYPE;

## 示例

```c
/*mrp code*/
#define GIF_IMAGE "OATfile\\pic_test\\image.gif"
T_DRAW_DIRECT_REQ
draw_direct = {0};
draw_direct.h = 40;
draw_direct.w =
40;
draw_direct.ox = 10;
draw_direct.oy = 10;
draw_direct.src =(char
*)GIF_IMAGE;
draw_direct.src_type = SRC_NAME ;
mrc_platEx( 3010, (uint8*)&amp;draw_direct, sizeof( T_DRAW_DIRECT_REQ),
NULL, NULL, NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
