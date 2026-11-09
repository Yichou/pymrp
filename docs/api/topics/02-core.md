# 02 · 核心运行时：内存与进程

> 内存申请释放、第二内存、内部 cache、扩展内存

本册收录 9 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_mem_get`

```c
int32 mr_mem_get (char** mem_base, uint32* mem_len)
```
**说明** 内存申请函数。
**参数** mem_base 返回的内存基地址; mem_len 返回的内存长度
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 当引擎正常启动时，引擎取得系统内存资源。该函数在SkyEngine引擎启动时只会调用一次，一次性取得所有需要的内存。在SkyEngine引擎启动之后，SkyEngine引擎会自己管理内存资源。
[全文](mr_mem_get.md)

#### `mr_mem_free`

```c
int32 mr_mem_free (char* mem, uint32 mem_len)
```
**说明** 内存释放接口。
**参数** mem 释放由mr_mem_get分配的内存; mem_len 内存大小，mr_mem_get返回的值
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
[全文](mr_mem_free.md)

#### `mr_printf`

```c
void mr_printf(const char *format, ...)
```
**说明** 调试信息打印。
**参数** format 格式化字符串
**返回** 无返回值.
[全文](mr_printf.md)

#### `mr_platEx(1001)` — 第二内存申请

```c
int32 mr_platEx (int32 code = 1001, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 第二内存申请。在某些内存紧张的平台中，sky
**参数** input 无; input_len 无; output 第二内存的地址; output_len 第二内存长度; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1001.md)

#### `mr_platEx(1002)` — 释放申请到的第二内存

```c
int32 mr_platEx (int32 code = 1002, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 释放申请到的第二内存。
**参数** input 第二内存的地址; input_len 第二内存长度; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-1002.md)

#### `mr_platEx(1012)` — 申请内部cache

```c
int32 mr_platEx (int32 code = 1012, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 申请内部cache。
**参数** input 要申请的buffer的大小; input_len 无; output 申请到的buffer的指针; output_len 无; cb 无
**返回** 一直返回MR_SUCCESS，需要判断*output的值, 未实现返回MR_IGNORE.
[全文](mr_platEx-1012.md)

#### `mr_platEx(1013)` — 释放申请内部cache

```c
int32 mr_platEx (int32 code = 1013, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 释放申请内部cache。
**参数** input 已经申请到的buffer的地址; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1013.md)

#### `mr_platEx(1014)` — 申请扩展内存

```c
int32 mr_platEx (int32 code = 1014, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 申请扩展内存。
**参数** input 无; input_len 要申请的buffer的大小; output 申请到的buffer的指针; output_len 申请到的内存的大小（和input_len相等）; cb 无
**返回** 一直返回成功，需要判断*output的值.
**备注** 这个函数管理了2个屏幕大小的buffer，但是这个buffer在切面切换，或者被pause的时候需要主动释放掉。
[全文](mr_platEx-1014.md)

#### `mr_platEx(1015)` — 释放扩展内存

```c
int32 mr_platEx (int32 code = 1015, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 释放扩展内存。
**参数** input 已经申请到的buffer的地址; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-1015.md)
