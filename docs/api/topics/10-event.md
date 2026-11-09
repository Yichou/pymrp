# 10 · 事件、定时器与生命周期

> mr_event 事件模型、定时器族、前后台切换、子应用加载（start_dsm）

本册收录 18 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_event`

```c
int32 mr_event(int16 type, int32 param1, int32 param2)
```
**说明** 发送事件给虚拟机，在应用层将通过mrc_event接收到相应的消息。
**参数** type 虚拟机预定义的事件类型，各个事件类型的具体定义请参考MR_EVENT_E; param1 参数1，由事件定义; param2 参数2，由事件定义
**返回** 当成功将事件发送到虚拟机并进行处理后将返回MR_SUCCESS, / 如果未将事件传到虚拟机将返回MR_FAILED，如果是虚拟机不支持的事件将返回MR_IGNORE。在返回值上这里有一点要特别注意，mr_event的返回值不等于mrc_event的返回值，某些时候我们可能期望通过mr_event来调用应用中的相应功能，但切记，通过mrc_event返回的值，在平台的移植层是得不到的。
**备注** 在移植层将本地的事件转换成虚拟机事件后，需要通过mr_event 将事件发送到虚拟机，应用层会由mrc_event接收，这里的发送是同步的，其实就是同步的调用过程，mr_event发送的事件遵循公共且唯一的定义，各个事件可带有1至2个参数，参数的个数和具体的移植由事件本身定义，应用和移植层遵循此协议。 事件定义 enum { MR_KEY_PRESS, /*按键按下事件, param1 为按键值*/ MR_KEY_RELEASE, /*1*/ MR_MOUSE_DOWN, /*2*/ MR_MOUSE_UP, /*3*/ MR_MENU_SELECT, /*4*/ MR_MENU_RETURN, /*5*/ MR_DIALOG_EVENT, /*6*/ MR_SMS_INDICATION, /*7*/ MR_EVENT_EXIT, /*8*/ MR_SMS_RESULT, /*9*/ MR…
[全文](mr_event.md)

#### `mr_timer`

```c
int32 mr_timer(void)
```
**说明** 定时器通知函数。
**参数**  
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 定时器到期时调用定时器事件，SkyEngine引擎将对之进行处理。
[全文](mr_timer.md)

#### `mr_timerStart`

```c
int32 mr_timerStart(uint16 t)
```
**说明** 定时器启动。
**参数** t 时间间隔，单位为毫秒
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 此定时器函数为单次函数，VM调用此函数来启动一次定时操作，但timeout后，需要调用外部移植接口mr_timer来通知VM。
[全文](mr_timerStart.md)

#### `mr_timerStop`

```c
int32 mr_timerStop(void)
```
**说明** 停止定时器。
**参数**  
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 用于停止mr_timerStart启动的定时器，如果之前没有调用过mr_timerStart,多调用此函数应该不会产生其他影响。
[全文](mr_timerStop.md)

#### `mr_pauseApp`

```c
int32 mr_pauseApp(void)
```
**说明** 暂停虚拟机。
**参数**  
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED。
**备注** 当有电话呼入或其他需要暂停应用的事件到来时，调用该函数暂停应用。
[全文](mr_pauseApp.md)

#### `mr_resumeApp`

```c
int32 mr_resumeApp(void)
```
**说明** 恢复虚拟机运行。
**参数**  
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
[全文](mr_resumeApp.md)

#### `mr_exit`

```c
int32 mr_exit(void)
```
**说明** 退出应用。
**参数**  
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 当用户选择退出应用时，SkyEngine应用调用该函数，通知系统释放资源。
[全文](mr_exit.md)

#### `mr_stop`

```c
int32 mr_stop(void)
```
**说明** 停止虚拟机，并释放相关资源。
**参数**  
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 退出SkyEngine并释放相关资源。引擎退出时会调用mr_mem_free函数释放由mr_mem_get函数取得的内存。
[全文](mr_stop.md)

#### `mr_registerAPP`

```c
int32 mr_registerAPP(uint8 *p, int32 len, int32 index)
```
**说明** 注册固化应用。
**参数** entry 固化应用的数据块内存指针; len 固化应用的数据块长度; index 1922版本起扩展到0-19）
**返回** 成功返回MR_SUCCESS, 失败返回MR_FIALED.
[全文](mr_registerAPP.md)

#### `mr_start_dsm`

```c
int32 mr_start_dsm(const char* entry)
```
**说明** 通过入口参数来启动虚拟机。
**参数** entry dsm入口标志，该标志用于启动非dsm根目录的项目。启动dsm根目录时该参数填NULL（相当于运行”*A”固化应用）。若该参数以’*’开头，则执行固化应用（参见“注册固化应用”小节），”*A”表示index为0的应用，”*B”表示index为1的应用，以此类推。若该参数以’%’开头，则执行根目录下的mrp文件，如”%QQ.mrp”执行QQ.mrp文件。
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 初始化SkyEngine引擎，并运行指定的应用。当SkyEngine引擎启动时会调用mr_mem_get获取引擎需要的内存。 mr_mem_get函数由移植者实现，以取得引擎需要的内存。entry是SkyEngine入口参数。
[全文](mr_start_dsm.md)

#### `mr_start_dsm_ex`

```c
int32 mr_start_dsm_ex(const char* path, const char* entry)
```
**说明** 通过入口参数来启动虚拟机。
**参数** path mrp文件路径; entry dsm入口标志，该标志用于启动非dsm根目录的项目。启动dsm根目录时该参数填NULL（相当于运行”*A”固化应用）。若该参数以’*’开头，则执行固化应用（参见“注册固化应用”小节），”*A”表示index为0的应用，”*B”表示index为1的应用，以此类推。若该参数以’%’开头，则执行根目录下的mrp文件，如”%QQ.mrp”执行QQ.mrp文件。
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 初始化SkyEngine引擎，并运行指定的应用。当SkyEngine引擎启动时会调用mr_mem_get获取引擎需要的内存。 mr_mem_get函数由移植者实现，以取得引擎需要的内存。entry是SkyEngine入口参数。
[全文](mr_start_dsm_ex.md)

#### `mr_start_dsmB`

```c
int32 mr_start_dsmB(const char* entry)
```
**说明** 直接启动mrp文件，并且可以传参过去。
**参数** entry dsm入口标志，该标志用于启动非dsm根目录的项目。启动dsm根目录时该参数填NULL（相当于运行”*A”固化应用）。若该参数以’*’开头，则执行固化应用（参见“注册固化应用”小节），”*A”表示index为0的应用，”*B”表示index为1的应用，以此类推。若该参数以’%’开头，则执行根目录下的mrp文件，如”%QQ.mrp”执行QQ.mrp文件。
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 此函数主要在非精简虚拟上用来直接启动mrp文件。
[全文](mr_start_dsmB.md)

#### `mr_start_dsmC`

```c
int32 mr_start_dsmC(const char* entry)
```
**说明** 通过入口参数来启动虚拟机。
**参数** entry dsm入口标志，该标志用于启动非dsm根目录的项目。启动dsm根目录时该参数填NULL（相当于运行”*A”固化应用）。若该参数以’*’开头，则执行固化应用（参见“注册固化应用”小节），”*A”表示index为0的应用，”*B”表示index为1的应用，以此类推。若该参数以’%’开头，则执行根目录下的mrp文件，如”%QQ.mrp”执行QQ.mrp文件。
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 初始化SkyEngine引擎，并运行指定的应用。当SkyEngine引擎启动时会调用mr_mem_get获取引擎需要的内存。 mr_mem_get函数由移植者实现，以取得引擎需要的内存。entry是SkyEngine入口参数。
[全文](mr_start_dsmC.md)

#### `mr_plat(1003)` — 激活后台程序到前台

```c
int32 mr_plat(int32 code = 1003, int32 param)
```
**说明** 将后台程序切换到前台运行。
**参数** param 要激活到前台的应用的appid
**返回** MR_SUCCESS ： 激活成功 / MR_FAILED ：激活失败 / MR_IGNORE / ：不支持该功能
**备注** 通知移植层将后台运行的应用激活到前台来运行。当激活后，移植层将通过mr_event()这个函数来通知应用。 注：mr_event 通知应用的参数说明： mr_event(MR_LOCALUI_EVENT, MR_LOCALUI_APPRESUME, 0); MR_LOCALUI_APPRESUME 2 MR_LOCALUI_EVENT 10
[全文](mr_plat-1003.md)

#### `mr_plat(1391)` — 查询是否支持后台接口

```c
int32 mr_plat(int32 code = 1391, int32 param)
```
**说明** 查询移植层是否支持后台运行接口。
**参数** param appid
**返回** MR_SUCCESS 表示支持 / MR_FAILED 不支持 / MR_IGNORE 不支持该功能
**备注** 如果该移植版本支持后台运行，那么返回的是MR_SUCCESS 。当前版本没有进行任何的条件判断；
[全文](mr_plat-1391.md)

#### `mr_platEx(1004)` — 切换到后台运行

```c
int32 mr_platEx (int32 code = 1004, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 后台运行。
**参数** input mr_backstage_st 结构的指针; input_len mr_backstage_st 结构的长度; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 通知移植层本应用需要后台运行 数据结构： typedef struct { int32 appid; //app id uint8 describe[20]; //应用标志符 - "ipqq" uint8* param; //预留扩展用 }mr_backstage_st;
[全文](mr_platEx-1004.md)

#### `mr_platEx(1323)` — 设置异步转后台

```c
int32 mr_platEx (int32 code = 1323, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置异步转后台。
**参数** input mr_backstage_async_runinfo_t 结构指针; input_len mr_backstage_async_runinfo_t 结构大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** typedef struct { uint32 bSilence; //客户端不需要提示是否退出后台应用 uint32 nTimerInterval; //延时启动的毫秒数 }mr_backstage_async_runinfo_t;
[全文](mr_platEx-1323.md)

#### `mr_platEx(6005)` — 停止异步转后台

```c
int32 mr_platEx (int32 code = 6005, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 停止异步转后台。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-6005.md)
