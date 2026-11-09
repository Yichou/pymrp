# mr_platEx(1005) - 在状态栏上显示图标

```c
int32 mr_platEx (int32 code = 1005, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

显示一张图片。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_pic_req 结构请求 |
| input_len | mr_pic_req 结构长度 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

请求移植层显示一张图片（图片显示的位置由移植来确定，可能在idle，或者icon条，或者两个地方都显示等等情况）
数据结构：
typedef
struct
{
int32 appid;
int32 time;
int32
img_type;
int32 img_size;
int32 width;
int32
height;
uint16 color;
uint8 *buff;
uint8
destId;
}mr_pic_req;
参数说明：
appid：请求画图的应用的id
time： 图片闪动的时间单位是：ms（毫秒）如果为0
表示不用闪动；
img_type:图片类型
0：BMP
图片；1：jpg 图片；2：png 图片；3：gif 图片
如果是bmp图片的话，buffer 指向的是解压后的点阵数据信息
img_size:buff 这个指针指向的空间的大小
color：
透明色（bmp 图片时候起作用）
buff： 图片数据。
destId:
0:表示画idle下的一个小图标
1：画idle下的整个背景
根据不同的timer大小，底层将确定进行怎样的操作
timer： 0
：显示icon但不闪动（如果是QQ显示在线图标）
1000：闪动的显示icon（如果是QQ显示在线图标）
1：显示离开状态的QQ头像（QQ专用）
2：显示隐身状态的QQ头像（QQ专用）
5：MRSTAR平台专用，用于mrp通知移植层，当前QQ已经启动可以实现end键转后台（QQ专用）；
1001：显示离开状态的QQ头像（QQ专用）
1002：显示隐身状态的QQ头像（QQ专用）
-1：为显示离线状态的QQ头像（QQ专用）

## 示例

```c
/*mrp code*/
void QQStateIconFicker(int32 appid, int32
timer)
{
mr_pic_req
picture;
memset(&amp;picture,0,sizeof(mr_pic_req));
picture.appid=appid;
picture.time =
timer;
picture.img_type =
0;
picture.color=
BM_TRANSPARENT;
picture.destId =
0;
mrc_platEx(1005,(uint8*)&amp;picture,
sizeof(mr_pic_req), 0, 0, 0);
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
