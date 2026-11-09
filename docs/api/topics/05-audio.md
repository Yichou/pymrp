# 05 · 声音与流媒体

> mr_playSound 一次性播放、mr_platEx 201x~225x 有状态播放器、PCM 环形缓冲、音量与铃声

本册收录 29 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_playSound`

```c
int32 mr_playSound(int type, const void* data, uint32 dataLen, int32 loop)
```
**说明** 播放音频。
**参数** type //8K; data 音频数据; datalen 数据长度; loop !=0，音乐循环播放；==0，单次播放
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 调用mr_playSound播放音频，调用mr_stopSound停止播放音频。
[全文](mr_playSound.md)

#### `mr_stopSound`

```c
int32 mr_stopSound (int type)
```
**说明** 停止播放音频。
**参数** type //8K
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
**备注** 调用mr_playSound播放音频，调用mr_stopSound停止播放音频。
[全文](mr_stopSound.md)

#### `mr_plat(102)` — 告知驱动PCM写入数据的绝对地址

```c
int32 mr_plat(int32 code = 102, int32 param)
```
**说明** 告知驱动PCM写入数据的绝对地址。（再根据数据的其实地址可以算出等待播放的数据量）
**参数** param PCM写入数据的绝对地址
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-102.md)

#### `mr_plat(103)` — 取得PCM数据已经播放掉的数据的绝对地址

```c
int32 mr_plat(int32 code = 103, int32 param)
```
**说明** 取得PCM数据已经播放掉的数据的绝对地址。
**参数** param 无
**返回** MR_IGNORE / 不支持该功能 / 其他 / 已经播放的的绝对地址
[全文](mr_plat-103.md)

#### `mr_plat(1302)` — 设置声音的大小

```c
int32 mr_plat(int32 code = 1302, int32 param)
```
**说明** 设置声音的大小。（播放时候的大小，非情景模式中的设置）。
**参数** param Engine中音量等级）
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1302.md)

#### `mr_plat(1213)` — 获得手机当前的情景模式

```c
int32 mr_plat(int32 code = 1213, int32 param)
```
**说明** 获得手机当前的情景模式。
**参数** param 无
**返回** 返回：MR_PLAT_VALUE_BASE+主题枚举值 / typedef / enum / { / MR_SCENE_NORMAL, / MR_SCENE_MEETING, / MR_SCENE_INDOOR, / MR_SCENE_OUTDOOR, / MR_SCENE_MUTE / }T_DSM_SCENE;
[全文](mr_plat-1213.md)

#### `mr_platEx(1208)` — 设置手机铃声

```c
int32 mr_platEx (int32 code = 1208, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置手机铃声。
**参数** input T_DSM_RING_SET结构的指针。; input_len T_DSM_RING_SET 结构的大小; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** MR_SUCCESS : 设置成功 / MR_FAILED : / 设置失败 / MR_IGNOR : 不支持该功能
**备注** 数据结构： pedef struct { int32 scene; int32 type; char *path; //gb编码 （相对VM当前目录的路径和歌曲名称） }T_DSM_RING_SET; Type： 0：MR_CALL_RING （来电铃声） 1：MR_SMS_RING （短信提示音） 2：MR_ALARM_RING （闹钟提示音） Scene： 0：MR_SCENE_NORMAL （一般模式） 1：MR_SCENE_MUTE （静音模式）
[全文](mr_platEx-1208.md)

#### `mr_platEx(201x)` — 设备初始化

```c
int32 mr_platEx (int32 code = 201x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设备初始化。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** platEx(201x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-201x.md)

#### `mr_platEx(202x)` — 加载一个文件

```c
int32 mr_platEx (int32 code = 202x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 加载一个文件。
**参数** input 文件名指针，文件名可以带路径; input_len 文件名长度; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** platEx(202x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-202x.md)

#### `mr_platEx(203x)` — 加载缓冲数据

```c
int32 mr_platEx (int32 code = 203x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 加载缓冲数据。
**参数** input LOAD_AUDIO_DATA_REQ数据结构指针; input_len LOAD_AUDIO_DATA_REQ数据结构长度; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** typedef struct { char* buf; //缓冲数据指针 int32 buf_len; //缓冲数据长度 }LOAD_AUDIO_DATA_REQ; platEx(203x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-203x.md)

#### `mr_platEx(204x)` — 从当前的位置开始播放

```c
int32 mr_platEx (int32 code = 204x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 从当前的位置开始播放。
**参数** input Block：1，阻塞播放；0，不阻塞播放; input_len 0 或 &gt;=12; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** platEx(204x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-204x.md)

#### `mr_platEx(205x)` — 暂停播放

```c
int32 mr_platEx (int32 code = 205x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 暂停播放。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** platEx(205x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-205x.md)

#### `mr_platEx(206x)` — 继续播放

```c
int32 mr_platEx (int32 code = 206x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 继续播放。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_WAITING 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** platEx(206x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-206x.md)

#### `mr_platEx(207x)` — 停止播放

```c
int32 mr_platEx (int32 code = 207x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 停止播放。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_WAITING 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** platEx(207x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-207x.md)

#### `mr_platEx(208x)` — 关闭设备

```c
int32 mr_platEx (int32 code = 208x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 关闭设备。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** platEx(208x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-208x.md)

#### `mr_platEx(209x)` — 获取当前设备的状态

```c
int32 mr_platEx (int32 code = 209x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取当前设备的状态。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_PLAT_VALUE_BASE + 设备状态值 / 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE / 不支持该功能 / 返回成功得到状态，其枚举值为: / typedef enum / tag_PLAY_STATE / { / MR_MEDIA_IDLE= 1001, /*1.not init; / 2.device closed*/ / MR_MEDIA_INITED = 1002, / MR_MEDIA_LOADED = 1003, /*1.loaded not play; 2.pl
**备注** platEx(209x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-209x.md)

#### `mr_platEx(210x)` — 设置播放位置，已经播放了多少时间

```c
int32 mr_platEx (int32 code = 210x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置播放位置，已经播放了多少时间。
**参数** input T_SET_PLAY_POS数据结构指针; input_len T_SET_PLAY_POS数据结构长度; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** typedef struct { int32 pos; //单位,秒s. }T_SET_PLAY_POS; platEx(210x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-210x.md)

#### `mr_platEx(211x)` — 设置播放位置，已经播放了相对文件或者缓冲的起始位置的偏移量

```c
int32 mr_platEx (int32 code = 211x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置播放位置，已经播放了相对文件或者缓冲的起始位置的偏移量。
**参数** input T_SET_PLAY_POS数据结构指针; input_len T_SET_PLAY_POS数据结构长度; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING / 异步模式，需要使用ACI_STATUS命令轮询以获取状态 / MR_IGNORE 不支持该功能
**备注** typedef struct { int32 pos; //pos：相对文件或者缓冲的起始位置的偏移量 }T_SET_PLAY_POS; platEx(211x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-211x.md)

#### `mr_platEx(212x)` — 获取整首歌的播放时间

```c
int32 mr_platEx (int32 code = 212x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取整首歌的播放时间。
**参数** input 无; input_len 无; output T_MEDIA_TIME数据结构指针; output_len T_MEDIA_TIME数据结构大小（字节数）; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持改功能
**备注** typedef struct { int32 pos; }T_MEDIA_TIME; platEx(212x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-212x.md)

#### `mr_platEx(213x)` — 获取当前的播放进度时间

```c
int32 mr_platEx (int32 code = 213x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取当前的播放进度时间。
**参数** input 无; input_len 无; output T_MEDIA_TIME数据结构指针; output_len T_MEDIA_TIME数据结构大小（字节数）; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** typedef struct { int32 pos;//pos：当前的播放进度时间，单位s。 }T_MEDIA_TIME; platEx(213x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-213x.md)

#### `mr_platEx(215x)` — 获取当前的播放进度时间

```c
int32 mr_platEx (int32 code = 215x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获取当前的播放进度时间。
**参数** input 无; input_len 无; output T_MEDIA_TIME数据结构指针; output_len T_MEDIA_TIME数据结构大小（字节数）; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE / 不支持该功能
**备注** typedef struct { int32 pos;//pos：当前的播放进度时间，单位ms。 }T_MEDIA_TIME; platEx(215x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-215x.md)

#### `mr_platEx(216x)` — 多媒体模块释放

```c
int32 mr_platEx (int32 code = 216x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 多媒体模块释放。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** platEx(216x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-216x.md)

#### `mr_platEx(220x)` — 占用IRAM

```c
int32 mr_platEx (int32 code = 220x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 占用IRAM。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** platEx(220x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-220x.md)

#### `mr_platEx(221x)` — 释放IRAM

```c
int32 mr_platEx (int32 code = 221x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 释放IRAM。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS / 成功 / MR_FAILED / 失败 / MR_IGNORE / 不支持该功能
**备注** platEx(221x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-221x.md)

#### `mr_platEx(222x)` — 多通道加载

```c
int32 mr_platEx (int32 code = 222x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 多通道加载。加载一个用于多通道的数据，目前只支持wav和midi 。
**参数** input T_BG_PLAY_REQ数据结构指针; input_len T_BG_PLAY_REQ数据结构大小; output 无; output_len 无; cb 无
**返回** MR_FAILED / 失败 / 其他 / 一个句柄，以后操作（播放，停止，关闭）都使用本句柄。
**备注** typedef struct { uint8 *data; uint32 len; int32 loop; }T_BG_PLAY_REQ; platEx(222x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-222x.md)

#### `mr_platEx(223x)` — 多通道播放已经加载的数据

```c
int32 mr_platEx (int32 code = 223x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 播放已经加载的数据。
**参数** input 指向句柄的值; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** platEx(223x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-223x.md)

#### `mr_platEx(224x)` — 多通道播放停止

```c
int32 mr_platEx (int32 code = 224x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 停止播放。
**参数** input 指向句柄的值; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** platEx(224x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-224x.md)

#### `mr_platEx(225x)` — 多通道释放已经加载的数据

```c
int32 mr_platEx (int32 code = 225x, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 释放已经加载的数据。
**参数** input 指向句柄的值; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS 成功 / MR_FAILED / 失败 / MR_IGNORE 不支持该功能
**备注** platEx(225x),其中x代表音频类型的枚举值： typedef enum tagT_MEDIA_TYPE { MEDIA_MIDI = 1, MEDIA_WAVE, MEDIA_MP3, MEDIA_AMR, MEDIA_PCM, MEDIA_M4A, MEDIA_AAC, MEDIA_LYRIC, MEDIA_UNKNOW }T_MEDIA_TYPE;
[全文](mr_platEx-225x.md)

#### `mr_plat(7)` — 按键音开启关闭控制

```c
int32 mr_plat(int32 code = 7, int32 param)
```
**说明** 按键音开启关闭控制。
**参数** param 0 关闭， 1 开启
**返回** MR_SUCCESS ： 成功 / MR_FAILED ： 失败 / MR_IGNORE ： / 不支持该功能
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。code的说明详见附录A。对于移植层不支持的code，移植层需要返回MR_IGNORE以告知VM和APP。
[全文](mr_plat-7.md)
