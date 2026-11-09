# 12 · 平台杂项与历史遗留

> NES 模拟器、平台 QQ、手柄、动感芯片、以及无归档的零散 code

本册收录 7 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_plat(4)` — nes特殊操作

```c
int32 mr_plat(int32 code = 4, int32 param)
```
**说明** nes特殊操作。
**参数** param 1：恢复
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
**备注** 关闭、恢复平台某些可能与nes模拟器冲突的资源。如：信息提示音、低压警告音等与nes的pcm播放冲突（iram资源。
[全文](mr_plat-4.md)

#### `mr_plat(5)` — 保存模拟器游戏积分

```c
int32 mr_plat(int32 code = 5, int32 param)
```
**说明** 保存模拟器游戏积分（覆盖式保存）。
**参数** param 保存积分数目
**返回** MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。
[全文](mr_plat-5.md)

#### `mr_plat(6)` — 读取模拟器游戏积分

```c
int32 mr_plat(int32 code = 6, int32 param)
```
**说明** 读取模拟器游戏积分。
**参数** param 无
**返回** MR_SUCCESS ： 成功 / MR_WAITING ： 未初始化（即首次读写） / MR_FAILED / ： 失败 / MR_IGNORE ： 不支持该功能
[全文](mr_plat-6.md)

#### `mr_plat(8)` — 设置wap下载的.nes保存所使用的存储器

```c
int32 mr_plat(int32 code = 8, int32 param)
```
**说明** 设置wap下载的.nes保存所使用的存储器。
**参数** param 第二外插存储设备
**返回** MR_SUCCESS ：成功 / MR_FAILED ：失败 / MR_IGNORE / ：不支持该功能
[全文](mr_plat-8.md)

#### `mr_platEx(1006)` — 启动平台QQ

```c
int32 mr_platEx (int32 code = 1006, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 启动平台QQ。
**参数** input mr_custStartParam_st结构的指针; input_len mr_custStartParam_st结构的长度; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。 输入参数如下： typedef struct { int32 appid; //sky应用唯一标志 uint8 describe[20]; //应用标志符 – 可填入list的启动参数as："mtkqq" uint8* param; //启动验证参数 int32 paramLen…
[全文](mr_platEx-1006.md)

#### `mr_platEx(1332) -SKYQQ接口`

```c
int32 mr_platEx (int32 code = 1332, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** SKYQQ接口。
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-1332.md)

#### `mr_platEx(1210)` — 获取NES模拟器按键布局

```c
int32 mr_platEx (int32 code = 1210, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取NES模拟器按键布局。
**参数** input 无; input_len 无; output mr_nes_keys_st结构的指针; output_len mr_nes_keys_st结构长度; cb 无
**返回** MR_SUCCESS : 成功 / MR_FAILED : 失败 / MR_IGNORE : / 不支持该功能
**备注** 数据结构： typedef struct _mr_nes_keys_st { uint8 k_up; uint8 k_down; uint8 k_left; uint8 k_right; uint8 k_se; uint8 k_st; uint8 k_a; uint8 k_b; uint8 auto_a; uint8 auto_b; }mr_nes_keys_st;
[全文](mr_platEx-1210.md)
