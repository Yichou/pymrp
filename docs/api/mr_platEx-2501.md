# mr_platEx(2501) - 进入预览状态

```c
int32 mr_platEx (int32 code = 2501, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

启动camera，进入preview状态。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_DSM_LAUNCH_CAMERA_REQ数据结构指针 |
| input_len | T_DSM_LAUNCH_CAMERA_REQ 数据结构大小 |
| output | T_DSM_COMMON_RSP数据结构指针地址 |
| output_len | T_DSM_COMMON_RSP数据结构大小 |
| cb | 无 |

## 返回值

MR_SUCCESS 成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 备注

数据结构如下，
typedef struct
{
uint32
preview_x; /*预览区域的x坐标*/
uint32 preview_y;
/*预览区域的y坐标*/
uint32
preview_w; /*预览区域的宽度*/
uint32
preview_h; /*预览区域的高度*/
uint32
img_w;
/*拍下来的照片的宽度*/
uint32
img_h; /*拍下来的照片的高度*/
uint32 img_qt;
/*图片质量*/
}T_DSM_LAUNCH_CAMERA_REQ;
typedef struct
{
int32 p1;
/*camera句柄*/
int32 p2;
/*osd层buffer*/
}T_DSM_COMMON_RSP;

## 示例

```c
/*mrp code*/
T_DSM_LAUNCH_CAMERA_REQ launch={0};
T_DSM_COMMON_RSP *cameRSP =
NULL;
int32 len;
launch.preview_h =
SCREEN_HEIGHT;
launch.preview_w = SCREEN_WIDTH;
launch.preview_x =
0;
launch.preview_y = 0;
launch.img_h = 32;
launch.img_w =
32;
launch.img_qt = 0;
mrc_platEx( 2501, (uint8*)&amp;launch,
sizeof ( T_DSM_LAUNCH_CAMERA_REQ ), (uint8**)&amp;cameRSP, (int32*)&amp;len,
NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
