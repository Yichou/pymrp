# 07 · 网络与连接

> socket 全套、DNS、WAP、APN、WIFI、连接状态与联网时长

本册收录 23 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_socket`

```c
int32 mr_socket(int32 type, int32 protocol)
```
**说明** 创建一个socket。
**参数** type MR_SOCK_DGRAM; protocol MR_IPPROTO_UDP
**返回** &gt;=0 socket句柄，MR_FAILED表示失败.
[全文](mr_socket.md)

#### `mr_connect`

```c
int32 mr_connect(int32 s, int32 ip, uint16 port, int32 type)
```
**说明** 建立 socket 连接。
**参数** s socket 句柄; ip 对端ip地址; port 对端端口号; type //非阻塞方式（异步方式）
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_WAITING 使用异步方式进行连接，VM需要轮询该socket的状态以获知连接状况
**备注** 初始化SkyEngine引擎，并运行指定的应用。当SkyEngine引擎启动时会调用mr_mem_get获取引擎需要的内存。 mr_mem_get函数由移植者实现，以取得引擎需要的内存。entry是SkyEngine入口参数。
[全文](mr_connect.md)

#### `mr_closeSocket`

```c
int32 mr_closeSocket(int32 s)
```
**说明** 关闭socket。
**参数** s socket 句柄
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
[全文](mr_closeSocket.md)

#### `mr_send`

```c
int32 mr_send(int32 s, const char *buf, int len)
```
**说明** 发送数据。
**参数** s socket 句柄; buf 待发送数据buffer; len 待发送数据长度
**返回** &gt;= 0表示实际发送数据的字节数，MR_FAILED表示出错.
[全文](mr_send.md)

#### `mr_recv`

```c
int32 mr_recv (int32 s, char *buf, int len)
```
**说明** 接收数据。
**参数** s socket 句柄; buf 接收数据缓冲区; len 缓冲区大小
**返回** &gt;=0表示实际接收的数据大小，MR_FAILED表示出错.
[全文](mr_recv.md)

#### `mr_sendto`

```c
int32 mr_sendto(int32 s, const char *buf, int len, int32 ip, uint16 port)
```
**说明** 发送数据报。
**参数** s socket句柄; buf 待发送数据buffer; len 待发送数据字节数; ip 对端IP; port 对端端口
**返回** &gt;=0表示实际发送的字节数，MR_FAILED表示出错.
[全文](mr_sendto.md)

#### `mr_recvfrom`

```c
int32 mr_recvfrom(int32 s, char *buf, int len, int32 *ip, uint16 *port)
```
**说明** 接受数据报。
**参数** s socket 句柄; buf 接收数据buffer; len buffer长度; ip 对端的IP地址; port 对端的端口号
**返回** &gt;=0表示实际接收到的数据字节数，MR_FAILED表示出错.
[全文](mr_recvfrom.md)

#### `mr_initNetwork`

```c
int32 mr_initNetwork(MR_INIT_NETWORK_CB cb, const char *mode)
```
**说明** 网络初始化。
**参数** cb 当网络初始化使用异步模式时，使用该回调函数通知引擎初始化结果; mode cmwap”的拨号方式。
**返回** MR_SUCCESS 同步模式，初始化成功，不再调用cb / MR_FAILED （立即感知的）失败，不再调用cb / MR_WAITING 使用回调函数通知引擎初始化结果.
**备注** 网络初始化，如果没有拨号，进行拨号操作。 这里需要注意的是，本文档描述的所有网络接口函数在实现时建议优先考虑采用非阻塞方式。 若网络初始化使用异步模式，使用回调函数通知引擎初始化结果。 typedef int32 (*MR_INIT_NETWORK_CB)(int32 result); 回调函数参数说明： result： MR_SUCCESS初始化成功 MR_FAILED 初始化失败
[全文](mr_initNetwork.md)

#### `mr_closeNetwork`

```c
int32 mr_closeNetwork(void)
```
**说明** 断开网络拨号。
**参数**  
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED.
[全文](mr_closeNetwork.md)

#### `mr_getHostByName`

```c
int32 mr_getHostByName(const char *name, MR_GET_HOST_CB cb)
```
**说明** 域名解析。
**参数** name 主机名; cb 回调函数
**返回** MR_FAILED （立即感知的）失败，不再调用cb / MR_WAITING 使用回调函数通知引擎获取IP的结果 / 其他值 同步模式，立即返回的IP地址，不再调用cb
**备注** 通过主机名获得该主机的IP地址值，如果一个主机的IP地址为218.18.95.203，则值为218&lt;&lt;24 + 18&lt;&lt;16 + 95&lt;&lt;8 + 203 = 0xda125fcb。 若获取主机IP使用异步模式，使用回调函数通知引擎获取IP的结果。 typedef int32 (*MR_GET_HOST_CB)(int32 ip); 回调函数参数说明： ip： MR_FAILED 获取IP失败 其他值 IP地址
[全文](mr_getHostByName.md)

#### `mr_getNetworkID`

```c
int32 mr_getNetworkID(void)
```
**说明** 获取网络ID。
**参数**  
**返回** 返回取值如下： / enum { / MR_NET_ID_MOBILE, / //移动GSM / MR_NET_ID_CN, // / 联通GSM / MR_NET_ID_CDMA, / //联通CDMA / MR_NET_ID_NONE / //未插卡或网络错误 / };
[全文](mr_getNetworkID.md)

#### `mr_connectWAP`

```c
void mr_connectWAP(char* wap)
```
**说明** 连接WAP。
**参数** wap url地址，长度不超过256
**返回** 无返回值.
[全文](mr_connectWAP.md)

#### `mr_plat(1001)` — 查询socket的连接状态

```c
int32 mr_plat(int32 code = 1001, int32 param)
```
**说明** 异步connect状态查询。
**参数** param Socket句柄
**返回** MR_SUCCESS ： 连接成功 / MR_FAILED ：连接失败 / MR_WAITING / ：连接中 / MR_IGNORE ：不支持该功能
**备注** 轮询 socket connect 状态（主要用于TCP的异步连接。）
[全文](mr_plat-1001.md)

#### `mr_plat(1002)` — 设置socket的连接等待时间

```c
int32 mr_plat(int32 code = 1002, int32 param)
```
**说明** 设置socketconnect等待时间“废止“。
**参数** param 超时时间，单位ms
**返回** MR_SUCCESS ： 设置成功 / MR_FAILED ：设置失败 / MR_IGNORE / ：不支持该功能
[全文](mr_plat-1002.md)

#### `mr_plat(1107)` — 发送获得apn信息的请求

```c
int32 mr_plat(int32 code = 1107, int32 param)
```
**说明** 发送获得apn信息的请求。
**参数** param 无
**返回** MR_WAITING ： / 发送成功 / MR_FAILED ： / 发送失败 / MR_IGNORE ： / 不支持该功能 / 注：处理结果通过mr_event返回给应用 / mr_event的参数如下： / 第一个：MR_DATA_ACCOUNT_EVENT（17） / 第二个：MR_DATA_ACCOUNT_OP_GET（0） / 第三个：MR_SUCCESS / 获取成功，apn信息已经放置在缓存中，MR_FAILED / 获取失败 / 当获取成功后调用mr_platEx(1108)获得缓冲中的内容
[全文](mr_plat-1107.md)

#### `mr_plat(1110)` — 设置apn使用的标志位

```c
int32 mr_plat(int32 code = 1110, int32 param)
```
**说明** 设置apn使用的标志位。
**参数** param 0：使用以前设置的值
**返回** MR_SUCCESS ：设置成功 / MR_FAILED ：设置失败 / MR_IGNORE / ：不支持该功能 / 注：本功能只使用海外的版本
[全文](mr_plat-1110.md)

#### `mr_plat(1111)` — 调用mtk的界面设置apn

```c
int32 mr_plat(int32 code = 1111, int32 param)
```
**说明** 调用mtk的界面设置apn。
**参数** param 无
**返回** MR_SUCCESS ：调用成功 / MR_FAILED ：调用失败 / MR_IGNORE / ：不支持该功能 / 注：调用本功能后VM会被pause
[全文](mr_plat-1111.md)

#### `mr_plat(1327)` — 查询WIFI是否可用

```c
int32 mr_plat(int32 code = 1327, int32 param)
```
**说明** 查询WIFI是否可用，这里的可用是只已经连上热点。
**参数** param 无
**返回** MR_SUCCESS 表示WIFI可用 / MR_FAILED 不可用 / MR_IGNORE 不支持该功能
[全文](mr_plat-1327.md)

#### `mr_plat(1328)` — 设置是否使用WIFI联网

```c
int32 mr_plat(int32 code = 1328, int32 param)
```
**说明** 设置是否使用WIFI联网。
**参数** param 非0：表示通过WIFI访问网络
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-1328.md)

#### `mr_platEx(1003)` — 绑定一个socket到本机端口

```c
int32 mr_platEx (int32 code = 1003, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 绑定一个socket到本机端口（udp）。
**参数** input mr_bind_st 结构的指针; input_len mr_bind_st 结构的长度; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构： typedef struct { int32 socket; //socket 句柄 int32 port; //端口号 }mr_bind_st;。
[全文](mr_platEx-1003.md)

#### `mr_platEx(1108)` — 从缓存中读取apn信息

```c
int32 mr_platEx (int32 code = 1108, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 从缓存中读取apn信息。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS : 请求成功 / MR_FAILED : 请求失败 / MR_IGNORE : / 不支持该功能
**备注** Apn的数据结果如下： typedef struct { uint8 authentication_type; uint8 user_name[32]; uint8 password[32]; uint8 dns[4]; uint8 apn[100]; }T_DSM_DATA_ACCOUNT;
[全文](mr_platEx-1108.md)

#### `mr_platEx(1109)` — 设置apn信息

```c
int32 mr_platEx (int32 code = 1109, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 设置apn信息。
**参数** input 指向T_DSM_DATA_ACCOUNT数据结构; input_len T_DSM_DATA_ACCOUNT的大小; output 无; output_len 无; cb 无
**返回** MR_WAITING : 请求成功 / MR_FAILED : 请求失败 / MR_IGNORE : / 不支持该功能
**备注** 设置结果异步通过mr_event返回， mr_event各个参数的值如下： 第一个参数：MR_DATA_ACCOUNT_EVENT（17） 第二个参数：MR_DATA_ACCOUNT_OP_SET（1） 第三个参数：MR_FAILED:设置失败 MR_SUCCESS:设置成功
[全文](mr_platEx-1109.md)

#### `mr_platEx(6004)` — 查询最后一次联网时间

```c
int32 mr_platEx (int32 code = 6004, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 查询当前SIM卡的最后一次联网时间。
**参数** input mr_datetime结构的指针; input_len mr_datetime结构的长度; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-6004.md)
