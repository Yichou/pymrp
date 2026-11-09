# 06 · 相机、录音与拍照

> camera 生命周期与变焦、预览取帧、拍照、录音与 PCM 取音

本册收录 15 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_plat(2500)` — 初始化

```c
int32 mr_plat(int32 code = 2500, int32 param)
```
**说明** 初始化camera。Parameters
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
**备注** 关闭camera，调用mr_plat(2504)。
[全文](mr_plat-2500.md)

#### `mr_plat(2502)` — 暂停

```c
int32 mr_plat(int32 code = 2502, int32 param)
```
**说明** 暂停camera。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2502.md)

#### `mr_plat(2503)` — 恢复

```c
int32 mr_plat(int32 code = 2503, int32 param)
```
**说明** 恢复camera到preview状态。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2503.md)

#### `mr_plat(2504)` — 关闭

```c
int32 mr_plat(int32 code = 2504, int32 param)
```
**说明** 关闭camera。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2504.md)

#### `mr_plat(2506)` — 获得缩放等级

```c
int32 mr_plat(int32 code = 2506, int32 param)
```
**说明** 获得camera的缩放等级。
**参数** param 无
**返回** 缩放等级+ MR_PLAT_VALUE_BASE
[全文](mr_plat-2506.md)

#### `mr_plat(2507)` — 放大

```c
int32 mr_plat(int32 code = 2507, int32 param)
```
**说明** camera 放大。
**参数** param 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2507.md)

#### `mr_plat(2508)` — 缩小

```c
int32 mr_plat(int32 code = 2508, int32 param)
```
**说明** camera 缩小。
**参数** param 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2508.md)

#### `mr_plat(2701)` — 暂停

```c
int32 mr_plat(int32 code = 2701, int32 param)
```
**说明** 录音暂停。
**参数** param 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2701.md)

#### `mr_plat(2702)` — 恢复

```c
int32 mr_plat(int32 code = 2702, int32 param)
```
**说明** 录音恢复。
**参数** param 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2702.md)

#### `mr_plat(2703)` — 停止

```c
int32 mr_plat(int32 code = 2703, int32 param)
```
**说明** 录音停止。
**参数** param 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-2703.md)

#### `mr_platEx(2501)` — 进入预览状态

```c
int32 mr_platEx (int32 code = 2501, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 启动camera，进入preview状态。
**参数** input T_DSM_LAUNCH_CAMERA_REQ数据结构指针; input_len T_DSM_LAUNCH_CAMERA_REQ 数据结构大小; output T_DSM_COMMON_RSP数据结构指针地址; output_len T_DSM_COMMON_RSP数据结构大小; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** 数据结构如下， typedef struct { uint32 preview_x; /*预览区域的x坐标*/ uint32 preview_y; /*预览区域的y坐标*/ uint32 preview_w; /*预览区域的宽度*/ uint32 preview_h; /*预览区域的高度*/ uint32 img_w; /*拍下来的照片的宽度*/ uint32 img_h; /*拍下来的照片的高度*/ uint32 img_qt; /*图片质量*/ }T_DSM_LAUNCH_CAMERA_REQ; typedef struct { int32 p1; /*camera句柄*/ int32 p2; /*osd层buffer*/ }T_DSM_COMMON_RSP;
[全文](mr_platEx-2501.md)

#### `mr_platEx(2505)` — 拍照

```c
int32 mr_platEx (int32 code = 2505, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 拍照。
**参数** input 2：单拍，需要调用mr_plat(2503)重新进入preview状态。; input_len sizeof(int32); output T_DSM_COMMON_RSP数据结构指针地址; output_len T_DSM_COMMON_RSP数据结构大小; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** 数据结构如下： typedef struct { int32 p1; /*图片buffer*/ int32 p2; /*图片大小*/ }T_DSM_COMMON_RSP;
[全文](mr_platEx-2505.md)

#### `mr_platEx(2509)` — 获取预览数据

```c
int32 mr_platEx (int32 code = 2509, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取预览数据。一旦调用该接口，则会获取预览数据，即使关闭了camera，任然在获取当前激活层的数据。
**参数** input 无; input_len 无; output T_LAYER_INFO数据结构指针地址; output_len T_LAYER_INFO数据结构大小; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** typedef struct { int32 handle; int32 w; int32 h; char *buffer; }T_LAYER_INFO;
[全文](mr_platEx-2509.md)

#### `mr_platEx(2700)` — 开始录音

```c
int32 mr_platEx (int32 code = 2700, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 开始录音。
**参数** input T_DSM_VOICE_REC_REQ数据结构指针; input_len T_DSM_VOICE_REC_REQ 数据结构大小; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** 数据结构如下： typedef struct { char *src; /*录音文件的相对文件名*/ int32 src_len; int32 src_type; int32 format; /* MR_SOUND_WAV , MR_SOUND_PCM , MR_SOUND_AMR , MR_SOUND_AMR_WB */ }T_DSM_VOICE_REC_REQ; 注：录音的异常情况通过mr_event通知，mr_event的参数如下： 第一个：MR_ERROR_EVENT 第二个：DSM_ERROR_NO_SPACE：空间满 MED_RES_TERMINATED：被中断 DSM_ERROR_UNKNOW：未知错误 第三个：0
[全文](mr_platEx-2700.md)

#### `mr_platEx(2704)` — 获得PCM数据

```c
int32 mr_platEx (int32 code = 2704, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 在录音启动的接口中将格式设置成pcm，src_type设置为SRC_STREAM的情况下，调用本接口来获得pcm数据
**参数** input 无; input_len 无; output pcm数据地址; output_len pcm数据的长度; cb 处理完本次pcm数据后需要调用的函数
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_platEx-2704.md)
