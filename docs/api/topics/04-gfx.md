# 04 · 图形、位图与图层

> 画位图、屏幕信息、字库、窗口、图层系统、PNG/GIF 解码、旋转与刷屏

本册收录 42 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_drawBitmap`

```c
void mr_drawBitmap(uint16* bmp, int16 x, int16 y, uint16 w, uint16 h)
```
**说明** 绘制BITMAP。
**参数** bmp 图片在内存中存放的地址首指针; x,y 图片左上角在屏幕中的坐标; w,h 图片高
**返回** 无返回值。
**备注** 将bmp指向的Bitmap图片绘制于屏幕中。bmp指向的图片格式是16bit色深的w*h大小的Bitmap图片，象素顺序是：从左上角的象素开始，从左到右，从上到下排列象素。每个象素的16bit的r,g,b分别为：5 bit、6 bit、5 bit。 如纯红色为：0b1111100000000000 如纯绿色为：0b0000011111100000 如纯篮色为：0b0000000000011111
[全文](mr_drawBitmap.md)

#### `mr_getScreenInfo`

```c
int32 mr_getScreenInfo(mr_screeninfo * screeninfo)
```
**说明** 获取屏幕信息。
**参数** screeninfo 返回屏幕信息数据结构mr_screeninfo
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 获取屏幕宽、高、象素深度等信息。 mr_screeninfo格式如下： typedef struct { uint32 width; //屏幕宽 uint32 height; //屏幕高 uint32 bit; //屏幕象素深度，单位bit，如：6万5千色（16bit色深）应该返回16。 }mr_screeninfo;
[全文](mr_getScreenInfo.md)

#### `mr_getCharBitmap`

```c
const char *mr_getCharBitmap(uint16 ch, uint16 fontSize, int *width, int *height)
```
**说明** 获取字符点整。
**参数** ch endian，比如“1”为0x0031若CPU是big endian，则该Unicode码是big endian，比如“1”为0x0031; fontSize MR_FONT_BIG合并；若支持一种字体，将所有字体合并。; width, height 返回的字符的宽和高
**返回** 放回字符的点整的起始地址，如果失败返回NULL. / 当字库里没有该字体的点阵信息是，希望不要返回失败，建议返回一个”口”这样的字体信息。
**备注** 获取unicode码ch指向的字体的点阵信息，并告之该字体的宽和高，获取到的点阵信息每一个bit表示字体的一个象素。目前的版本字体每行的象素都是以紧凑的方式排布，即不按字节对齐的方式。 注：若字库中的字体每行的象素必须按字节对齐，也就是说如果一个字体宽为12，则需要用两个字节来表示该信息，第二个字节的后四个bit为0，从第三个字节开始才表示下一行的点阵数据。则需要特别编译特殊的版本。
[全文](mr_getCharBitmap.md)

#### `mr_winCreate`

```c
int32 mr_winCreate(void)
```
**说明** 创建可扩展窗体。
**参数**  
**返回** &gt;0 为窗体句柄，MR_FAILED表示失败.
**备注** 创建一个可扩展窗体，并返回可扩展窗体句柄。可扩展窗体是一种可动态下载更新的窗体模式，可动态扩充功能，可以实现进度条、扩展控件、交互小应用等等强大的扩充功能。 可扩展窗体创建之后，需要将用户的按键和触摸屏事件构造成SkyEngine消息，通过mr_event函数传送给SkyEngine，按键事件的消息类型为MR_KEY_PRESS、MR_KEY_RELEASE，触摸屏事件的消息类型为MR_MOUSE_DOWN、MR_MOUSE_UP。
[全文](mr_winCreate.md)

#### `mr_winRelease`

```c
int32 mr_winRelease(int32 win)
```
**说明** 释放窗体。
**参数** win 可扩展窗体句柄
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
[全文](mr_winRelease.md)

#### `mr_plat(101)` — 设置旋转角度

```c
int32 mr_plat(int32 code = 101, int32 param)
```
**说明** 设置图象旋转显示的角度。
**参数** param 7：MR_LCD_MIRROR_ROTATE_270
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-101.md)

#### `mr_plat(104)` — 销毁窗口而不画屏幕

```c
int32 mr_plat(int32 code = 104, int32 param)
```
**说明** 销毁窗口而不画屏幕。（BASE WIN以上的窗口都销毁）。
**参数** param 无
**返回** MR_IGNORE ：不支持该功能 / MR_SUCCESS：销毁成功
**备注** 这个接口会负责把base win以上的创建对象和申请的资源都释放掉， 要在启动另外一个应用之前调用这个接口，调用了这个接口之后只需 要销毁VM中的窗口，请不要再调用d_release 之类的释放本地接口 函数。
[全文](mr_plat-104.md)

#### `mr_plat(105)` — 获取旋转角度

```c
int32 mr_plat(int32 code = 105, int32 param)
```
**说明** 获取旋转角度。（未实现）
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-105.md)

#### `mr_plat(1020)` — 获得当前背光状态

```c
int32 mr_plat(int32 code = 1020, int32 param)
```
**说明** 获得当前背光状态x18x。
**参数** param 无
**返回** 1000 ： 背光灭 / 其他值 ：背光亮
[全文](mr_plat-1020.md)

#### `mr_plat(1310)` — 释放层

```c
int32 mr_plat(int32 code = 1310, int32 param)
```
**说明** 释放层。
**参数** param 层句柄
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1310.md)

#### `mr_plat(1312)` — 设置激活层

```c
int32 mr_plat(int32 code = 1312, int32 param)
```
**说明** 设置激活层。
**参数** param 层句柄
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1312.md)

#### `mr_plat(1314)` — 设置png的背景层

```c
int32 mr_plat(int32 code = 1314, int32 param)
```
**说明** 设置png的背景层。
**参数** param 层句柄
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1314.md)

#### `mr_plat(1317)` — 设置层的透明值

```c
int32 mr_plat(int32 code = 1317, int32 param)
```
**说明** 设置层的透明值。
**参数** param 值的范围在0～255之间（0：不透，255：全透）。
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1317.md)

#### `mr_plat(1318)` — 关闭层的透明属性

```c
int32 mr_plat(int32 code = 1318, int32 param)
```
**说明** 关闭层的透明属性。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1318.md)

#### `mr_plat(1319)` — 设置层的透明色

```c
int32 mr_plat(int32 code = 1319, int32 param)
```
**说明** 设置层的透明色（透明色是纯蓝色）。
**参数** param 值的范围在0～255之间（0：不透，255：全透）。
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1319.md)

#### `mr_plat(1320)` — 关闭层的透明色处理

```c
int32 mr_plat(int32 code = 1320, int32 param)
```
**说明** 关闭层的透明色处理。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1320.md)

#### `mr_plat(1321)` — 设置刷屏锁

```c
int32 mr_plat(int32 code = 1321, int32 param)
```
**说明** 设置刷屏锁后，之后的刷屏动作都无效
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1321.md)

#### `mr_plat(1322)` — 取消刷屏锁

```c
int32 mr_plat(int32 code = 1322, int32 param)
```
**说明** 需要在调用刷屏锁之后匹配调用 。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1322.md)

#### `mr_plat(1325)` — 绘制主菜单背景

```c
int32 mr_plat(int32 code = 1325, int32 param)
```
**说明** 绘制主菜单的背景（直接绘制的当前激活层上）。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1325.md)

#### `mr_plat(1326)` — 控制状态栏显示

```c
int32 mr_plat(int32 code = 1326, int32 param)
```
**说明** 控制状态条是否显示。
**参数** param 0：关闭或者不显示状态条
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1326.md)

#### `mr_plat(3012)` — 停止动画

```c
int32 mr_plat(int32 code = 3012, int32 param)
```
**说明** 动画停止。
**参数** param mr_platEx(3011)得到的句柄
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
[全文](mr_plat-3012.md)

#### `mr_platEx(1201)` — 获取字宽字高

```c
int32 mr_platEx (int32 code = 1201, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取字宽字高。这个接口主要为了解决某些平台字宽字高不等的情况。这个接口返回在该平台上最大的字宽和字高。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_IGNORE ： 不支持该功能 / 其他 ： 0～7bit 中文字宽 / 8～15bit / 中文字高 / 16～23bit 英文字宽 / 24～31bit 英文字高
[全文](mr_platEx-1201.md)

#### `mr_platEx(1207)` — UNICODE 转 GB

```c
int32 mr_platEx (int32 code = 1207, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** unicode转gb。
**参数** input Unicode字符串指针。//大端; input_len Unicode字符串长度，Unicode字符串以”\0\0”结尾，该值仅做参考。; output 返回的GB字符串缓冲; output_len 返回的GB字符串缓冲的长度。; cb 无
**返回** MR_SUCCESS ：转换成功 / MR_FAILED ：转换失败 / MR_IGNORE / ：不支持该功能
**备注** Unicode字符串到gb字符串的转换。Unicode字符串以”\0\0”结尾，输入的“Unicode字符串长度”从Mythroad传下，仅有参考价值。
[全文](mr_platEx-1207.md)

#### `mr_platEx(1308)` — 设置参与刷新的层

```c
int32 mr_platEx (int32 code = 1308, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置参与刷新的层的句柄的列表。
**参数** input 指向T_BLT的指针; input_len T_BLT大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构： typedef struct { int32 layer1; int32 layer2; int32 layer3; int32 layer4; }T_BLT;
[全文](mr_platEx-1308.md)

#### `mr_platEx(1309)` — 创建层

```c
int32 mr_platEx (int32 code = 1309, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 创建层。
**参数** input 指向T_LAYER_CREATE的指针; input_len T_LAYER_CREATE大小; output }T_DSM_COMMON_RSP;; output_len T_DSM_COMMON_RSP 大小; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构： typedef struct { int32 x; int32 y; int32 w; int32 h; int32 size; char *buffer; }T_LAYER_CREATE;
[全文](mr_platEx-1309.md)

#### `mr_platEx(1311)` — 获得base层的句柄

```c
int32 mr_platEx (int32 code = 1311, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得base层的句柄。
**参数** input 指向T_LAYER_CREATE的指针; input_len T_LAYER_CREATE大小; output }T_DSM_COMMON_RSP;; output_len T_DSM_COMMON_RSP大小; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1311.md)

#### `mr_platEx(1313)` — 设置层位置

```c
int32 mr_platEx (int32 code = 1313, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置层位置。
**参数** input 指向T_LAYER_POS的指针; input_len T_LAYER_POS大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构： typedef struct { int32 x; int32 y; }T_LAYER_POS;
[全文](mr_platEx-1313.md)

#### `mr_platEx(1315)` — 获取激活层信息

```c
int32 mr_platEx (int32 code = 1315, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取激活层信息。
**参数** input 无; input_len 无; output 层信息结构指针; output_len 层信息结构大小; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1315.md)

#### `mr_platEx(1316)` — 层叠加

```c
int32 mr_platEx (int32 code = 1316, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 进行层叠加。
**参数** input 指向T_LAYER_FLATTEN的指针; input_len T_LAYER_FLATTEN大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 将layer1，layer2，layer3，layer4，的数据叠加后放置在deslayer层中 数据结构： typedef struct { int32 desLayer; int32 layer1; int32 layer2; int32 layer3; int32 layer4; }T_LAYER_FLATTEN;
[全文](mr_platEx-1316.md)

#### `mr_platEx(3001)` — 获取图片信息

```c
int32 mr_platEx (int32 code = 3001, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取图片信息。
**参数** input MRAPP_IMAGE_ORIGIN_T数据结构指针; input_len MRAPP_IMAGE_ORIGIN_T数据结构大小; output IMAGE_INFO数据结构指针地址; output_len IMAGE_INFO数据结构大小（字节数）; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** 输入数据结构： typedef struct { char *src; //当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径 int32 len; //当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0 int32 src_type; // 枚举MRAPP_SRC_TYPE } MRAPP_IMAGE_ORIGIN_T; typedef enum { SRC_NAME = 0, //传到移植接口的是文件名 SRC_STREAM //传到移植接口的是图片数据流 }MRAPP_SRC_TYPE; 输出数据结构： typedef struct { int32 width; //图片的宽度 int32 height; //图片的高度 }IMAGE_INFO;
[全文](mr_platEx-3001.md)

#### `mr_platEx(3002)` — 图片解码

```c
int32 mr_platEx (int32 code = 3002, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 解码一张图片，将解完的数据放到dest所指的buf中，并通知vm解码结果。（gif不在此中处理）。
**参数** input MRAPP_IMAGE_DECODE_T数据结构指针; input_len MRAPP_IMAGE_DECODE_T数据结构大小; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用命令轮询以获取状态 / MR_IGNORE / 不支持该功能 / (注1：特殊平台可能有特殊返回值处理，当前不做考虑)
**备注** 输入数据结构： typedef struct { char *src; //当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径 int32 len; //当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0 int32 width; //图片宽度 int32 height; //图片高度 int32 src_type; // 枚举MRAPP_SRC_TYPE char *dest; //rgb565 bmp格式(注1) } MRAPP_IMAGE_DECODE_T; typedef enum { SRC_NAME = 0, //传到移植接口的是文件名 SRC_STREAM //传到移植接口的是图片数据流 }MRAPP_SRC_TYPE;
[全文](mr_platEx-3002.md)

#### `mr_platEx(3003)` — 查询解码状态

```c
int32 mr_platEx (int32 code = 3003, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 取得图像解码状态（异步解码）。未实现。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** MR_SUCCESS / 解码成功 / MR_FAILED / 解码失败 / MR_WAITING / 正在解码 / MR_IGNORE / 不支持该功能
[全文](mr_platEx-3003.md)

#### `mr_platEx(3004)` — gif解码

```c
int32 mr_platEx (int32 code = 3004, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 解码一张GIF图片，将解完的数据放到dest所指的buf中，并通知vm解码结果。
**参数** input MRAPP_IMAGE_DECODE_T数据结构指针; input_len MRAPP_IMAGE_DECODE_T数据结构大小; output MRAPP_GIF_HEADER数据结构指针地址; output_len MRAPP_GIF_HEADER数据结构大小; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** 输入数据结构： typedef struct { char *src; //文件名或是数据流的buf的地址，如果是文件名，是GB格式 int32 len; //src所指的buf的大小 int32 width; //用于图片显示的区域的宽度 int32 height; //用于图片显示的区域的高度 int32 src_type; // 枚举MRAPP_SRC_TYPE char *dest; //解码后的图片数据存放的buffer }MRAPP_IMAGE_DECODE_T; typedef enum { SRC_NAME = 0, //传到移植接口的是文件名 SRC_STREAM //传到移植接口的是图片数据流 }MRAPP_SRC_TYPE; 输出数据结构： typedef struct { int32 id; int32 width; //gif的宽度 int32 height; /…
[全文](mr_platEx-3004.md)

#### `mr_platEx(3005)` — 释放gif解码资源

```c
int32 mr_platEx (int32 code = 3005, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 应用通知移植层释放先前gif解码（mr_platEx（3004））用到的资源。
**参数** input MRAPP_GIF_HEADER数据结构指针（mr_platEx（3004）返回的指针）; input_len MRAPP_GIF_HEADER数据结构大小; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
[全文](mr_platEx-3005.md)

#### `mr_platEx(3007)` — 绘制BUFFER

```c
int32 mr_platEx (int32 code = 3007, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 绘制BUFFER。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED 失败 / MR_IGNORE / 不支持该功能
**备注** case MR_DRAW_BUFFER: { gdi_enable_non_block_blt(); GDI_LAYER_SET_FLAG(gdi_act_layer,GDI_LAYER_FLAG_FROZEN); gdi_layer_blt_previous(0,0, GDI_LAYER.width-1,GDI_LAYER.height-1); GDI_LAYER_CLEAR_FLAG(gdi_act_layer,GDI_LAYER_FLAG_FROZEN); return MR_SUCCESS; }
[全文](mr_platEx-3007.md)

#### `mr_platEx(3008)` — 获取ACTIVE LAYER

```c
int32 mr_platEx (int32 code = 3008, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取active layer。
**参数** input 无; input_len 无; output gdi_layer_struct数据结构指针; output_len gdi_layer_struct数据结构大小; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** typedef struct gdi_layer_struct { U32 id; U32 flag; S32 layer_size; /* bytes */ U16 width, height; S16 clipx1, clipy1, clipx2, clipy2; U8 *buf_ptr; U8 *buf_ptr1; gdi_rect_struct clips[GDI_LAYER_CLIP_STACK_COUNT]; U8 bits_per_pixel; U8 clips_top; U8 cf; /* real color format ( it will support LCD color format) */ U8 vcf; /* virtual color format (convert to standard color format) */ gd_get_pixel_func…
[全文](mr_platEx-3008.md)

#### `mr_platEx(3009)` — DMA异步刷屏

```c
int32 mr_platEx (int32 code = 3009, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 直接刷屏（非阻塞形式)。
**参数** input 显示缓冲; input_len 缓冲大小; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED 失败 / MR_IGNORE / 不支持该功能
[全文](mr_platEx-3009.md)

#### `mr_platEx(3010)` — 直接调用平台接口将图片绘制到指定的矩形内

```c
int32 mr_platEx (int32 code = 3010, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 直接调用平台接口将图片绘制到指定的矩形内。
**参数** input T_DRAW_DIRECT_REQ数据结构指针; input_len T_DRAW_DIRECT_REQ数据结构大小; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** 输入数据结构： typedef struct { char *src; //当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径 int32 src_len; //当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0 int32 src_type; //枚举MRAPP_SRC_TYPE int32 ox; //图片显示在x坐标 int32 oy; //图片显示在y坐标 int32 w; //图片宽度 int32 h; //图片高度 }T_DRAW_DIRECT_REQ; typedef enum { SRC_NAME = 0, //传到移植接口的是文件名 SRC_STREAM //传到移植接口的是图片数据流 }MRAPP_SRC_TYPE;
[全文](mr_platEx-3010.md)

#### `mr_platEx(3011)` — 显示gif动画

```c
int32 mr_platEx (int32 code = 3011, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 显示gif动画的接口（直接绘制到frame
**参数** input T_DRAW_DIRECT_REQ数据结构指针; input_len T_DRAW_DIRECT_REQ数据结构大小; output T_DSM_COMMON_RSP数据结构指针; output_len T_DSM_COMMON_RSP数据结构大小; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** 输入数据结构： typedef struct { char *src; //当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径 int32 src_len; //当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0 int32 src_type; //枚举MRAPP_SRC_TYPE int32 ox; //图片显示在x坐标 int32 oy; //图片显示在y坐标 int32 w; //图片宽度 int32 h; //图片高度 }T_DRAW_DIRECT_REQ; typedef enum { SRC_NAME = 0, //传到移植接口的是文件名 SRC_STREAM //传到移植接口的是图片数据流 }MRAPP_SRC_TYPE; 输出数据结构： ty…
[全文](mr_platEx-3011.md)

#### `mr_platEx(3013)`

```c
int32 mr_platEx (int32 code = 3013, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** MR_SET_ANIMATION_BLT_CB，未实现。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-3013.md)

#### `mr_platEx(3014)` — 绘制mtk资源格式的图片

```c
int32 mr_platEx (int32 code = 3014, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 绘制mtk资源格式的图片。
**参数** input T_DRAW_DIRECT_REQ数据结构指针; input_len T_DRAW_DIRECT_REQ数据结构大小; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** 输入数据结构： typedef struct { char *src; int32 src_len; int32 src_type; int32 ox; int32 oy; int32 w; int32 h; }T_DRAW_DIRECT_REQ;
[全文](mr_platEx-3014.md)

#### `mr_platEx(3015)` — 绘制mtk资源格式的gif动画

```c
int32 mr_platEx (int32 code = 3015, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 绘制mtk资源格式的gif动画。动画停止需要调用mr_plat(3012,句柄)。
**参数** input T_DRAW_DIRECT_REQ数据结构指针; input_len T_DRAW_DIRECT_REQ数据结构大小（字节数）; output T_DSM_COMMON_RSP数据结构指针; output_len T_DSM_COMMON_RSP数据结构大小; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** 输入数据结构： typedef struct { char *src; //当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径 int32 src_len; //当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0 int32 src_type; //枚举MRAPP_SRC_TYPE int32 ox; //图片显示在x坐标 int32 oy; //图片显示在y坐标 int32 w; //图片宽度 int32 h; //图片高度 }T_DRAW_DIRECT_REQ; typedef enum { SRC_NAME = 0, //传到移植接口的是文件名 SRC_STREAM //传到移植接口的是图片数据流 }MRAPP_SRC_TYPE; 输出数据结构： ty…
[全文](mr_platEx-3015.md)
