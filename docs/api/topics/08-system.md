# 08 · 系统、时间与设备状态

> 时间日期、系统信息、SIM 与信号、背光与主题、震动与传感器、语言与时区、闹钟天气

本册收录 55 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_getTime`

```c
uint32 mr_getTime(void)
```
**说明** 获取毫秒时间。
**参数**  
**返回** 当前的毫秒时间.
**备注** 获取系统时间，单位毫秒。系统时间可以以SkyEngine引擎启动之前的任意时刻为起始时间，返回从起始时间到目前经过的毫秒数。例如这个函数可以实现为返回系统启动后经过的毫秒数。
[全文](mr_getTime.md)

#### `mr_getDatetime`

```c
int32 mr_getDatetime(mr_datetime* datetime)
```
**说明** 获取当前的日期。
**参数** datetime 日期时间
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 获取系统日期时间。 mr_datetime格式如下： typedef struct { uint16 year; //年 uint8 month; //月 uint8 day; //日 uint8 hour; //时，24小时制 uint8 minute; //分 uint8 second; //秒 }mr_datetime;
[全文](mr_getDatetime.md)

#### `mr_sleep`

```c
int32 mr_sleep(uint32 ms)
```
**说明** 让当前任务睡眠ms毫秒。方便调试的接口，可实现为空。
**参数** ms 睡眠时间，单位为毫秒
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
[全文](mr_sleep.md)

#### `mr_info`

```c
int32 mr_info(const char* filename)
```
**说明** 获取文件属性。
**参数** filename 文件名
**返回** 返回取值如下. / #define MR_IS_FILE 1//是文件 / #define / MR_IS_DIR 2//是目录 / #define MR_IS_INVALID / 8//文件不存在，或既不是文件也不是目录
[全文](mr_info.md)

#### `mr_getUserInfo`

```c
int32 mr_getUserInfo(mr_userinfo* info)
```
**说明** 获取手机相关信息。
**参数** info 手机信息
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 返回手机相关信息。mr_userinfo说明如下： typedef struct { uint8 IMEI[16]; //IMEI len eq 15 uint8 IMSI[16]; //IMSI len not more then 15 char manufactory[8]; //厂商名，最大7个字符，空字节填\0 char type[8]; //mobile type，最大7个字符，空字节填\0 uint32 ver; //移植版本, 参考移植版本号规则 uint8 spare[12]; //备用 }mr_userinfo;
[全文](mr_getUserInfo.md)

#### `mr_newSIMInd`

```c
int32 mr_newSIMInd(int16 type, uint8* old_IMSI)
```
**说明** 用户SIM卡变更通知。
**参数** type //未进行换卡操作，当前SkyEngine忽略该情况; old_IMSI 长度为16字节的旧IMSI号指针，若type为MR_SIM_NEW或MR_SIM_SAME，置为NULL
**返回** 成功返回MR_SUCCESS, 失败返回MR_FAILED, 不关心返回MR_IGNORE。
**备注** 通知SkyEngine引擎，用户插入了新的SIM卡(包括第一次使用该手机和换卡操作)。当新手机插入SIM卡，或者用户进行换卡消息时，通知SkyEngine引擎进行备份。建议在短消息模块初始化完成后，调用该函数，确保该函数能正确执行。
[全文](mr_newSIMInd.md)

#### `mr_startShake`

```c
int32 mr_startShake(int32 ms)
```
**说明** 启动震动。
**参数** ms 震动持续的毫秒数
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
[全文](mr_startShake.md)

#### `mr_plat(1)` — 调节CPU频率

```c
int32 mr_plat(int32 code = 1, int32 param)
```
**说明** 调节cpu频率。
**参数** param 其他值：不变
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-1.md)

#### `mr_plat(2)` — 获取平台可映射虚拟键数

```c
int32 mr_plat(int32 code = 2, int32 param)
```
**说明** 获取平台可映射虚拟键数目。
**参数** param 无定义
**返回** MR_PLAT_VALUE_BASE + 键数目 / MR_IGNORE 不支持该功能
[全文](mr_plat-2.md)

#### `mr_plat(3)` — 获取虚拟键状态

```c
int32 mr_plat(int32 code = 3, int32 param)
```
**说明** 获取虚拟键对应的按下、弹起状态。
**参数** param 虚拟键的index
**返回** MR_PLAT_VALUE_BASE + 0 ： 弹起（un-pressed） / MR_PLAT_VALUE_BASE + / 1 ： / 按下（pressed） / MR_IGNORE / ： 不支持该功能
[全文](mr_plat-3.md)

#### `mr_plat(1004)` — 设置使用SIM卡

```c
int32 mr_plat(int32 code = 1004, int32 param)
```
**说明** 多sim卡待机时设置所用sim卡。
**参数** param 中simId，由手机或移植处定义）
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-1004.md)

#### `mr_plat(1006)` — 隐藏状态栏上的图标

```c
int32 mr_plat(int32 code = 1006, int32 param)
```
**说明** 停止在idle上显示图标或者idle背景。
**参数** param 应用编号
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-1006.md)

#### `mr_plat(1011)` — 设置收到新短信的时候是否显示提示界面

```c
int32 mr_plat(int32 code = 1011, int32 param)
```
**说明** 设置收到新短信的时候是否显示提示界面。
**参数** param 0：不显示新短信提示
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-1011.md)

#### `mr_plat(1016) -初始化`

```c
int32 mr_plat(int32 code = 1016, int32 param)
```
**说明** 初始化信号强度。
**参数** param 无
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-1016.md)

#### `mr_plat(1018)` — 关闭

```c
int32 mr_plat(int32 code = 1018, int32 param)
```
**说明** 关闭获得信号强度功能。
**参数** param 无
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-1018.md)

#### `mr_plat(1113)` — 还原手机主题

```c
int32 mr_plat(int32 code = 1113, int32 param)
```
**说明** 还原手机主题。
**参数** param 无
**返回** MR_SUCCESS ： 设置成功 / MR_FAILED ：设置失败 / MR_IGNORE / ：不支持该功能
[全文](mr_plat-1113.md)

#### `mr_plat(1114)` — 获得当前激活的主题的appid

```c
int32 mr_plat(int32 code = 1114, int32 param)
```
**说明** 获得当前激活的主题的app id。
**参数** param 无
**返回** &gt;1000 ： 当前激活的主题的app id是返回值-1000 / 1000：当前没有设置主题 / MR_FAILED / ：设置失败 / MR_IGNORE ：不支持该功能
[全文](mr_plat-1114.md)

#### `mr_plat(1115)` — 设置主题中主菜单当前选中的宫格的index

```c
int32 mr_plat(int32 code = 1115, int32 param)
```
**说明** 设置主题中主菜单当前选中的宫格的index。
**参数** param 宫格index
**返回** MR_SUCCESS ： 设置成功 / MR_FAILED ：设置失败 / MR_IGNORE / ：不支持该功能
[全文](mr_plat-1115.md)

#### `mr_plat(1205)` — 获取手机是否是触摸屏信息

```c
int32 mr_plat(int32 code = 1205, int32 param)
```
**说明** 获取手机是否是触摸屏信息。
**参数** param 无
**返回** MR_PLAT_VALUE_BASE + 0 ：非触摸屏 / MR_PLAT_VALUE_BASE + 1 / ：触摸屏 / MR_FAILED / ：获取失败 / MR_IGNORE / ：不支持该功能
[全文](mr_plat-1205.md)

#### `mr_plat(1206)` — 获取手机当前设置的语言

```c
int32 mr_plat(int32 code = 1206, int32 param)
```
**说明** 获取手机当前设置的语言。
**参数** param 无
**返回** MR_PLAT_VALUE_BASE + 0 ：中文 / MR_PLAT_VALUE_BASE + 1 / ：英文 / MR_FAILED / ：获取失败 / MR_IGNORE / ：不支持该功能 / 注：其他语言的键值可以放在“英文”之后返
[全文](mr_plat-1206.md)

#### `mr_plat(1211)` — 生成随机数

```c
int32 mr_plat(int32 code = 1221, int32 param)
```
**说明** 调用平台接口产生随即数。
**参数** param 无
**返回** 要产生的随即数的范围(正整数) / 返回：MR_PLAT_VALUE_BASE + 随机数 / ：产生随即数成功 / MR_FAILED / ：产生随机数失败 / MR_IGNORE / ：不支持该功能
[全文](mr_plat-1211.md)

#### `mr_plat(1214)` — 设置挂机键是否回IDLE

```c
int32 mr_plat(int32 code = 1214, int32 param)
```
**说明** 屏幕该界面下按挂机键回idle的功能。
**参数** param 0：打开
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE / 不支持该功能
[全文](mr_plat-1214.md)

#### `mr_plat(1215)` — 初始化

```c
int32 mr_plat(int32 code = 1215, int32 param)
```
**说明** 获得cell id的初始化。
**参数** param 无
**返回** MR_SUCCESS：成功 / MR_FAILED：失败 / MR_IGNORE：不支持该功能
[全文](mr_plat-1215.md)

#### `mr_plat(1216)` — 关闭

```c
int32 mr_plat(int32 code = 1216, int32 param)
```
**说明** 关闭获得cell id功能。
**参数** param 无
**返回** MR_SUCCESS：成功 / MR_FAILED：失败 / MR_IGNORE：不支持该功能
[全文](mr_plat-1216.md)

#### `mr_plat(1217)` — 退出天气预报

```c
int32 mr_plat(int32 code = 1217, int32 param)
```
**说明** 退出天气预报。
**参数** param 无
**返回** MR_SUCCESS：成功 / MR_FAILED：失败 / MR_IGNORE：不支持该功能
[全文](mr_plat-1217.md)

#### `mr_plat(4001)` — 停止动感芯片监听

```c
int32 mr_plat(int32 code = 4001, int32 param)
```
**说明** 停止动感芯片监听。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-4001.md)

#### `mr_plat(4002)` — 给动感芯片上电

```c
int32 mr_plat(int32 code = 4002, int32 param)
```
**说明** 给动感芯片上电。
**参数** param Engine中音量等级）
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-4002.md)

#### `mr_plat(4003)` — 给动感芯片断电

```c
int32 mr_plat(int32 code = 4003, int32 param)
```
**说明** 给动感芯片断电。
**参数** param Engine中音量等级）
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-4003.md)

#### `mr_plat(4004)` — 动感芯片监听晃动模式

```c
int32 mr_plat(int32 code = 4004, int32 param)
```
**说明** 动感芯片监听晃动模式。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
**备注** 晃动的值将通过mr_event值来传递 mr_event(p1,p2,p3); p1: MR_MOTION_EVENT(18) p2: MR_MOTION_EVENT_SHAKEA(0) p3:指向这个数据结构的指针： typedef struct { int32 x; //重力加速速度在x方向的分量 int32 y; //重力加速速度在y方向的分量 int32 z; //重力加速速度在z方向的分量 }T_MOTION_ACC;
[全文](mr_plat-4004.md)

#### `mr_plat(4005)` — 动感芯片进入监听晃动的模式

```c
int32 mr_plat(int32 code = 4005, int32 param)
```
**说明** 设置动感芯片监听倾斜模式。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
**备注** 晃动的值将通过mr_event值来传递 mr_event(p1,p2,p3); p1: MR_MOTION_EVENT(18) p2: MR_MOTION_EVENT_SHAKEA(1) p3:指向这个数据结构的指针： typedef struct { int32 x; //重力加速速度在x方向的分量 int32 y; //重力加速速度在y方向的分量 int32 z; //重力加速速度在z方向的分量 }T_MOTION_ACC;
[全文](mr_plat-4005.md)

#### `mr_plat(4006)` — 获取动感芯片上送的数值的范围值

```c
int32 mr_plat(int32 code = 4006, int32 param)
```
**说明** 获取动感芯片上送的数值的范围值 。
**参数** param 无
**返回** &gt;1000 成功 返回值A那么动感芯片上送的值的范围在（-（A-1000）到（A-1000）） / MR_FAILED / 失败 / MR_IGONRE / 不支持该功能 / 注：以上动感芯片x,y,z坐标做如下定义： / 1、 当手机平放的时候，Z方向正值最大。 / 2、 当手机平盖的时候，Z方向负值最大 / 3、 当手机屏幕向左，横立起来的时候，X方向正值最大； / 4、 当手机屏幕向右，横立起来的时候，X方向负值最大； / 5、 当屏幕对着自己的时候，竖立起来的时候，Y方向负值最大； / 6、 当屏幕背向着自己的时候，竖立起来的时候，Y方向正值最大
[全文](mr_plat-4006.md)

#### `mr_platEx(0x90001)` — 获取当前时区信息

```c
int32 mr_platEx (int32 code = 0x90001, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取当前时区信息。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-0x90001.md)

#### `mr_platEx(0x90002)`

```c
int32 mr_platEx (int32 code = 0x90002, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取手机支持的全部语言。
**参数** input 无; input_len 无; output 支持的语言数组，int32 数组; output_len 数组的大小; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-0x90002.md)

#### `mr_platEx(1005)` — 在状态栏上显示图标

```c
int32 mr_platEx (int32 code = 1005, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 显示一张图片。
**参数** input mr_pic_req 结构请求; input_len mr_pic_req 结构长度; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 请求移植层显示一张图片（图片显示的位置由移植来确定，可能在idle，或者icon条，或者两个地方都显示等等情况） 数据结构： typedef struct { int32 appid; int32 time; int32 img_type; int32 img_size; int32 width; int32 height; uint16 color; uint8 *buff; uint8 destId; }mr_pic_req; 参数说明： appid：请求画图的应用的id time： 图片闪动的时间单位是：ms（毫秒）如果为0 表示不用闪动； img_type:图片类型 0：BMP 图片；1：jpg 图片；2：png 图片；3：gif 图片 如果是bmp图片的话，buffer 指向的是解压后的点阵数据信息 img_size:buff 这个指针指向的空间的大小 color： 透明色（bm…
[全文](mr_platEx-1005.md)

#### `mr_platEx(1017)` — 获得信号强度

```c
int32 mr_platEx (int32 code = 1017, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得信号强度。
**参数** input 无; input_len 无; output 指向T_RX 的指针; output_len T_RX结构大小; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE. / 注：需要调用mr_plat中的1016和1018进行初始化和退出
**备注** 数据结构： typedef struct { uint8 level; uint8 current_band; uint8 rat; uint8 flag; }T_RX;。
[全文](mr_platEx-1017.md)

#### `mr_platEx(1112)` — 激活手机主题

```c
int32 mr_platEx (int32 code = 1112, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 激活手机主题。
**参数** input 相对于根目录的目录 gb编码; input_len 字符串长度; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1112.md)

#### `mr_platEx(1116)` — 获取编译时间

```c
int32 mr_platEx (int32 code = 1116, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取编译时间。
**参数** input 无; input_len 无; output 编译时间字符串，如"2010/09/26 21:36"; output_len 字符串长度+1; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1116.md)

#### `mr_platEx(1117)` — 获取硬件版本号

```c
int32 mr_platEx (int32 code = 1117, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取硬件版本号。
**参数** input 无; input_len 无; output 版本好字符串; output_len 字符串长度+1; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1117.md)

#### `mr_platEx(1222)` — 设置背光一直为开

```c
int32 mr_platEx (int32 code = 1222, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置lcd一直为开，lcd 不进入sleep。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1222.md)

#### `mr_platEx(1223)` — 恢复背光设置

```c
int32 mr_platEx (int32 code = 1223, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 恢复lcd 设置，lcd 可定时进入sleep。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1223.md)

#### `mr_platEx(1224)` — 获取小区ID

```c
int32 mr_platEx (int32 code = 1224, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取小区ID等部分信息。
**参数** input 无; input_len 无; output 指向T_DSM_CELL_INFO 的指针; output_len T_DSM_CELL_INFO结构大小; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构： typedef struct { uint16 lac; uint16 cell_id; uint8 mnc[2]; uint8 mcc[3]; uint8 mnc3[4];/*移植版本x15x后增加的字段，mnc3[0]中表示的mnc的第三位*/ }T_DSM_CELL_INFO; 注：需要调用mr_plat中的1215和1216进行初始化和退出
[全文](mr_platEx-1224.md)

#### `mr_platEx(1225)` — 获取手柄信息

```c
int32 mr_platEx (int32 code = 1225, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取手柄信息。
**参数** input MRAPP_HANDLE_CODE_T结构的指针。; input_len MRAPP_HANDLE_CODE_T结构的大小; output 指向MRAPP_HANDLE_INFO_T 的指针; output_len MRAPP_HANDLE_INFO_T结构大小; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构： typedef struct { uint32 state; //手柄标志，目前使用 //0 bit：手柄状态，0手柄未插入； // 1手柄已插入。 uint8 k_up; //按键上，当值为：0 未按下， 1 按下， 下同 uint8 k_down; //按键下 uint8 k_left; //按键左 uint8 k_right; //按键右 uint8 k_select; //按键 “选择” uint8 k_start; //按键 “开始” uint8 k_a; //按键 A uint8 k_b; //按键 B uint8 k_auto_a; //按键 自动A uint8 k_auto_b; //按键 自动B uint8 k_c; //按键 其他，保留 uint8 k_d; //按键 其他，保留 uint8 k_left_up; //按键 左上 uint8 k_left_d…
[全文](mr_platEx-1225.md)

#### `mr_platEx(1226)` — 获取PLMN

```c
int32 mr_platEx (int32 code = 1226, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得当前网络的id。
**参数** input 无; input_len 无; output 网络id（字符串ascii）; output_len id数据的长度; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-1226.md)

#### `mr_platEx(1307)` — 获取SIM卡个数信息

```c
int32 mr_platEx (int32 code = 1307, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得sim卡个数等信息。
**参数** input 无; input_len 无; output MR_DUALSIM_SET_T结构的指针; output_len MR_DUALSIM_SET_T结构大小；; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 用来获取多卡多待手机当前的sim状态信息。如果是非多卡多待手机，可以直接返回MR_IGNORE； 数据结构： typedef struct { uint8 totalNum; //sim numbers, max to 6 uint8 curActive; //index of simId[] witch actived uint16 dummy; //no use, just for align int32 simId[4]; //mapping to plat sim socket id char* simNamePtr[4]; //sim卡名字,unicode uint16 simNameLen[4]; //名字长度 }MR_DUALSIM_SET_T;
[全文](mr_platEx-1307.md)

#### `mr_platEx(5001)` — 获取手机时间

```c
int32 mr_platEx (int32 code = 5001, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取手机时间。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-5001.md)

#### `mr_platEx(5002)` — 设置手机时间

```c
int32 mr_platEx (int32 code = 5002, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置手机时间。
**参数** input 指向MYTIME数据结构; input_len MYTIME 的大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构如下， typedef struct MYTIME { kal_uint16 nYear; kal_uint8 nMonth; kal_uint8 nDay; kal_uint8 nHour; kal_uint8 nMin; kal_uint8 nSec; kal_uint8 DayIndex; } MYTIME;
[全文](mr_platEx-5002.md)

#### `mr_platEx(5011)` — 设置手机闹钟

```c
int32 mr_platEx (int32 code = 5011, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置手机闹钟。（未实现）
**参数** input 指向mr_alarm_set_req_struct结构的指针; input_len mr_alarm_set_req_struct大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构： typedef struct { UINT8 alarm_index;/*第几个闹铃*/ UINT8 recurr;/*一个星期哪一天闹铃*/ DSMTIME dsm_time; }mr_alarm_set_req_struct; 说明:闹钟设置只针对 小时,分.
[全文](mr_platEx-5011.md)

#### `mr_platEx(5013)` — 获得手机闹钟个数

```c
int32 mr_platEx (int32 code = 5013, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得手机闹钟个数。（未实现）
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-5013.md)

#### `mr_platEx(5014)` — 设置闹钟

```c
int32 mr_platEx (int32 code = 5014, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置闹钟,到时间,启动获得天气的应用。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-5014.md)

#### `mr_platEx(5015)` — 获得天气信息

```c
int32 mr_platEx (int32 code = 5015, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得天气信息。
**参数** input t_mr_weather_info; input_len 输入参数大小（字节数）; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构定义 .天气情况: typedef enum { E_SUNNY, //晴 E_RAIN,//雨天 E_SNOW,//雪 E_CLOUDY,//多云 }e_weather_info; 时间结构 typedef struct { int hour; int min; }t_sun_time; 日期结构 typedef struct { int year; int month; int day; }t_dsm_date; 天气信息 typedef struct { int weather;// 天气 int high;//最高温度 int low;//最低温度 int wind;//风力 int barometerj;//大气压强 int humidity;//湿度 int visibility ;//可见度 int dewpoint;//露点 t_sun_time sunrise;/…
[全文](mr_platEx-5015.md)

#### `mr_platEx(5016)` — 进入天气预报

```c
int32 mr_platEx (int32 code = 5016, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 进入天气预报。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-5016.md)

#### `mr_platEx(5017)` — 退出天气预报

```c
int32 mr_platEx (int32 code = 5017, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 退出天气预报。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-5017.md)

#### `mr_platEx(5018)` — 获取天气通知

```c
int32 mr_platEx (int32 code = 5018, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取天气通知。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-5018.md)

#### `mr_platEx(5019)` — 获取天气桌面信息

```c
int32 mr_platEx (int32 code = 5019, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取天气桌面信息。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-5019.md)

#### `mr_platEx(1009)` — 设置墙纸

```c
int32 mr_platEx (int32 code = 1009, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置墙纸。
**参数** input 指向T_SET_IDLE_PAPER_REQ数据结构; input_len T_SET_IDLE_PAPER_REQ 的大小; output 无; output_len 无; cb 无
**返回** MR_WAITING : 请求成功 / MR_FAILED : 请求失败 / MR_IGNORE : / 不支持该功能
**备注** 数据结构如下， typedef struct { int32 setType;/* MR_IDLE_BG_PAPER 墙纸，MR_IDLE_SAVER_PAPER屏保*/ U8 *filename;/*图片的相对路径*/ }T_SET_IDLE_PAPER_REQ;
[全文](mr_platEx-1009.md)
