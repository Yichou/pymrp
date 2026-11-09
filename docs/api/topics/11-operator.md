# 11 · 短信、电话本与运营商

> 短信收发与信箱、彩信、电话本（本地与非本地 UI）、本机号码

本册收录 25 个接口。内容由手册正文自动抽取，未作改写。

#### `mr_sendSms`

```c
int32 mr_sendSms(char* pNumber, char*pContent, int32 flags)
```
**说明** 发送一条短信。
**参数** pNumber 电话号码，ASCII码; pContent 消息内容，ASCII码或Unicode码，由flags参数决定; flags bit：保留
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED, / 未准备好返回MR_IGNORE.
[全文](mr_sendSms.md)

#### `mr_smsIndiaction`

```c
int32 mr_smsIndiaction(uint8 *pContent, int32 nLen, uint8 *pNum, int32 type)
```
**说明** 新消息提示。
**参数** pContent 接收到的短信内容; nLen 短信内容长度; pNum 短信发送者号码; type 网络字节序
**返回** 操作成功返回MR_SUCCESS,操作失败返回MR_FAILED,不处理返回MR_IGNORE. / 在返回非MR_IGNORE的情况下需要删除该短信。
**备注** 当手机收到短消息时调用该函数。该函数检测新来的消息是否为SkyEngine配置消息，如果是SkyEngine配置消息，则进行对应的配置操作，返回MR_SUCCESS或MR_FAILED；不是SkyEngine配置消息则返回MR_IGNORE。每当手机收到新来的短消息，调用这个接口，如果返回值是MR_SUCCESS或MR_FAILED，则需要丢弃(删除)该消息。如果返回值是MR_IGNORE，该消息不是SkyEngine配置消息，无须进行特殊处理。
[全文](mr_smsIndiaction.md)

#### `数据账号接口`

```c
MTK平台账号资料管理流程 Mythroad 联网流程介绍 (TCP) 初始化网络（mr_initNetwork）-&gt;创建连接（mr_socket） -&gt;连接服务器（mr_connect）-&gt;收发数据(mr_recv, mr_send) -&gt;关闭连接（mr_closeSocket）-&gt;断开网络（mr_closeNetwork） MTK账号资料管理介绍 在mtk上账号资料分为两类： A、 GSM账号资料（电路交换方式） B、 GPRS账号资料 每种账号一般留有10个槽位（槽位个数手机设计公司可以进行调节）在创建socket的时候，有一个参数就是指这个账号资料的序号。目前Mythroad固定使用GPRS账号的最后一个槽位. 国内账号资料管理流程 在程序初始化网络（即调用mr_initNetwork）的时候，根据不通的拨号方式（CMNET,CMWAP，默认是CMNET）对指定槽位的账号资料进行设置（不论是否已经设置过，都会进行设置）。 优点：用户不需要关心账号资料的设置 缺点：如果是运营商的对联网的账号资料进行修改的话，就会造成无法连接网络的情况出现。 手机wap账号资料的管理 在wap的菜单中有这样一个菜单： 进入这个菜单后，会把手机上有的账号资料在列表中罗列出来供用户进行选择。 新账号资料管理方案（适用国内和海外） 流程图 新增接口 1、 本地UI设置账号资料接口 2、 设置账号资料接口 3、 读取账号资料接口 4、 设置是否使用当前设置接口（默认是不使用当前设置，设置的结果只对一次VM运行起作用，重新启动VM后自动复位） 优缺点 优点： 1、 账号资料可以完全保密 2、 实现复杂度低 缺点： 1、 检索的表是预置的无法修改（添加、删除） 2、 当表中没有记录的时候需要用户来设置（增加用户使用的难度） 代码实现 国内目前的实现： 国内现在拨号流程基本如下，工具用户的参数，拨CMWAP或者CMNET。 海外： 自动模式： 根据当前的MCC/MNC查询APN的数据库，如果有匹配项就使用匹配的APN信息进行拨号，如果出海外，你还得带上mr_getAPN接口的实现。 手动模式： 通过用户选择特定的数据账号，并将其保存下来。拨号的时候使用这个账号的信息进行拨号。 MTK上CODE的参考定义 #define MR_GET_DATA_ACCOUNT_REQ 1107 //mr_plat #define MR_GET_DATA_ACCOUNT 1108 //mr_platEx #define MR_SET_DATA_ACCOUNT 1109 //mr_platEx #define MR_SET_DATA_ACCOUNT_USE_FLAG 1110 //mr_plat #define MR_SET_DATA_ACCOUNT_MTK_UI 1111 // mr_plat MR_GET_DATA_ACCOUNT_REQ 功能：发起获取数据账号的请求，在MTK上为异步方式，这个CODE需要配和MR_GET_DATA_ACCOUNT来取的数据账号的值 参数：无 返回：失败MR_FAILED, 获取过程中返回MR_WAITING，成功MR_SUCCESS 如果是异步返回的，获取成功后需要通知虚拟机，如下： mr_event(MR_DATA_ACCOUNT_EVENT, MR_DATA_ACCOUNT_OP_GET, ret); 下面是2个枚举值在的定义，第3个参数 MR_SUCCESS 表示成功，MR_FAILED表示失败 enum { MR_KEY_PRESS, /*0*/ MR_KEY_RELEASE, /*1*/ MR_MOUSE_DOWN, /*2*/ MR_MOUSE_UP, /*3*/ MR_MENU_SELECT, /*4*/ MR_MENU_RETURN, /*5*/ MR_DIALOG_EVENT, /*6*/ MR_SMS_INDICATION, /*7*/ MR_EVENT_EXIT, /*8*/ MR_SMS_RESULT, /*9*/ MR_LOCALUI_EVENT, /*10*/ MR_OSD_EVENT, /*11*/ MR_MOUSE_MOVE, /*12*/ MR_ERROR_EVENT, /*13执行异常通过这个事件来通知*/ MR_PHB_EVENT, MR_SMS_OP_EVENT, MR_SMS_GET_SC, MR_DATA_ACCOUNT_EVENT, MR_MOTION_EVENT, }; enum { MR_DATA_ACCOUNT_OP_GET, MR_DATA_ACCOUNT_OP_SET, }; MR_GET_DATA_ACCOUNT 功能：返回由MR_GET_DATA_ACCOUNT_REQ发起获取的数据账号值 参数通过: output, output_len参数返回类型为T_DSM_DATA_ACCOUNT 的数据账号（这个结构的内存为移植层的全局数据，不需要应用层管理） 返回：MR_SUCCESS 表示成功，MR_FAILED表示失败 typedef struct { uint8 authentication_type; uint8 user_name[32]; uint8 password[32]; uint8 dns[4]; uint8 apn[100]; }T_DSM_DATA_ACCOUNT; MR_SET_DATA_ACCOUNT 功能：设置数据账号 参数：input, input_len 为T_DSM_DATA_ACCOUNT结构类型的数据 返回：MR_SUCCESS 成功，MR_FAILED失败，MR_WAITING异步过程通过后续事件通知应用mr_event(MR_DATA_ACCOUNT_EVENT,MR_DATA_ACCOUNT_OP_SET,MR_FAILED); 前面两个参数参考MR_GET_DATA_ACCOUNT_REQ节的定义，第三个参数MR_SUCCESS表示成功，MR_FAILED表示失败。 MR_SET_DATA_ACCOUNT_USE_FLAG 功能：启用设置的数据账号 参数：0 表示使用原先的拨号流程，1，表示使用设置的数据账号 返回：成功MR_SUCCESS, 失败MR_FAILED MR_SET_DATA_ACCOUNT_MTK_UI 功能：通过启用本地的界面显示全部可选的系统数据账号让用户选择，用户选择后，将选择的账号信息，保存到我们指定的数据账号中。 参数：无 返回：MR_SUCCESS,MR_FAILED Copyright ?2005-20010 SKY-MOBI
```
[全文](数据账号接口.md)

#### `电话本接口`

```c
电话本事件说明 1、 电话本的操作事件采用mr_event的形式通知上层应用。 2、 Mr_event的三个参数的具体说明如下： Mr_event(p1,p2,p3); p1 = 14 p2 = 0：添加条目 1：读取条目/*未使用*/ 2：修改条目 3：删除条目 p3 =MR_FAILED 操作失败 MR_SUCCESS 操作成功 Copyright ?2005-20010 SKY-MOBI
```
[全文](电话本接口.md)

#### `mr_call`

```c
void mr_call(char * pNumber)
```
**说明** 拨打电话。
**参数** pNumber 电话号码
**返回** 无返回值.
[全文](mr_call.md)

#### `mr_plat(1100)` — 获得短信操作的状态

```c
int32 mr_plat(int32 code = 1100, int32 param)
```
**说明** 获得短信操作的状态。
**参数** param 无
**返回** MR_SMS_NOT_READY = MR_PLAT_VALUE_BASE：短信模块初始化中 / MR_SMS_READY= / MR_PLAT_VALUE_BASE+1 ：短信模块初始化完毕可以操作。
[全文](mr_plat-1100.md)

#### `mr_plat(1101)` — 获得短信信箱中短息的条数

```c
int32 mr_plat(int32 code = 1101, int32 param)
```
**说明** 获得短信信箱中短息的条数。
**参数** param }MR_MSG_STATUS;
**返回** MR_FAILED：操作失败 / 短信条数加上MR_PLAT_VALUE_BASE。
[全文](mr_plat-1101.md)

#### `mr_plat(1106)` — 获得短信中心

```c
int32 mr_plat(int32 code = 1106, int32 param)
```
**说明** 发送获得短信中心的号码的请求。
**参数** param 应用编号
**返回** MR_WAITING ： 发送请求成功 / MR_FAILED ：设置失败 / MR_IGNORE / ：不支持该功能 / 注：处理结果通过mr_event返回给应用 / mr_event的参数如下： / 第一个：MR_SMS_GET_SC（16） / 第二个：ascii编码的短信中心的字符串的地址，地址为0标志获得失败 / 第三个：0
[全文](mr_plat-1106.md)

#### `mr_plat(4017)` — 拷贝记录

```c
int32 mr_plat(int32 code = 4017, int32 param)
```
**说明** 拷贝一条记录。（没实现）
**参数** param Engine中音量等级）
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-4017.md)

#### `mr_plat(4022)` — 获取本机号码

```c
int32 mr_plat(int32 code = 4022, int32 param)
```
**说明** 获得本机号码。（无实现）
**参数** param Engine中音量等级）
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-4022.md)

#### `mr_plat(4031)` — 删除所有记录

```c
int32 mr_plat(int32 code = 4031, int32 param)
```
**说明** 删除所有记录。（无实现）
**参数** param Engine中音量等级）
**返回** MR_SUCCESS 成功 / MR_FAILED 失败 / MR_IGNORE 不支持该功能
[全文](mr_plat-4031.md)

#### `mr_platEx(1008)` — 调用mtk的发送短信界面

```c
int32 mr_platEx (int32 code = 1008, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 调用mtk的发送短信界面。
**参数** input 指向T_PLAT_SENDSMS_REQ 数据结构; input_len T_PLAT_SENDSMS_REQ 的大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** 数据结构如下， typedef struct { char *pNum;/*目前没有使用该参数*/ char *pContent;/*大端unicode*/ }T_PLAT_SENDSMS_REQ;。
[全文](mr_platEx-1008.md)

#### `mr_platEx(1102)` — 获得指定一条短信的信息

```c
int32 mr_platEx (int32 code = 1102, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得指定一条短信的信息。
**参数** input 指向T_DSM_GET_SMS_INFO_REQ; input_len T_DSM_GET_SMS_INFO_REQ大小; output 无; output_len 无; cb 无
**返回** MR_WAITING : 请求成功 / MR_FAILED : 请求失败 / MR_IGNORE : / 不支持该功能
**备注** 短信的数据结构是：T_DSM_MSG_INFO 数据结果如下： typedef struct { int32 index;//显示时候索引 int8 type; //MR_SMS_INBOX, MR_SMS_OUTBOX }T_DSM_GET_SMS_INFO_REQ; typedef struct { int8 t_stamp [6]; /*t_stamp[0]年t_stamp[1]月t_stamp[2]日 t_stamp[3]时t_stamp[4]分t_stamp[5]秒*/ int8 num[21]; /*发送方号码*/ int8 sms_status; /*Read or Unread */ int8 sms_storage; /* MR_SMS_STORAGE_ME , MR_SMS_STORAGE_SIM*/ }T_DSM_MSG_INFO;
[全文](mr_platEx-1102.md)

#### `mr_platEx(1103)` — 读取一条短信

```c
int32 mr_platEx (int32 code = 1103, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 读取一条短信。
**参数** input 指向T_DSM_GET_SMS_INFO_REQ; input_len T_DSM_GET_SMS_INFO_REQ大小; output 无; output_len 无; cb 无
**返回** MR_WAITING : 请求成功 / MR_FAILED : 请求失败 / MR_IGNORE : / 不支持该功能
**备注** 读取结果： 通过mr_event通知应用，各个参数的含义如下： 第一个：MR_SMS_OP_EVENT 第二个：MR_SMS_OP_GET_MSG_CONTENT 第三个：短信内容缓存的地址（编码方式是大端unicode） 数据结果如下： typedef struct { int32 index;//显示时候索引 int8 type; //MR_SMS_INBOX, MR_SMS_OUTBOX }T_DSM_GET_SMS_INFO_REQ;
[全文](mr_platEx-1103.md)

#### `mr_platEx(1104)` — 删除一条短信

```c
int32 mr_platEx (int32 code = 1104, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 删除一条短信。
**参数** input 指向T_DSM_DELETE_SMS_REQ; input_len T_DSM_DELETE_SMS_REQ大小; output 无; output_len 无; cb 无
**返回** MR_WAITING : 请求成功 / MR_FAILED : 请求失败 / MR_IGNORE : / 不支持该功能
**备注** 删除结果： 通过mr_event通知应用，各个参数的含义如下： 第一个：MR_SMS_OP_EVENT 第二个：MR_SMS_OP_DELETE 第三个：MR_SUCCESS 删除成功 MR_FAILED 删除失败 数据结果如下： typedef struct { int32 index;//显示时候索引 int8 type; //MR_SMS_INBOX, MR_SMS_OUTBOX } T_DSM_DELETE_SMS_REQ;
[全文](mr_platEx-1104.md)

#### `mr_platEx(1203)` — 发送彩信

```c
int32 mr_platEx (int32 code = 1203, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 调用发送彩信功能。
**参数** input mr_mms_st结构指针; input_len mr_mms_st结构大小; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** typedef struct { char* addr; //接收地址指针,ASCII uint16* content; //预设内容指针，大端unicode }mr_mms_st;
[全文](mr_platEx-1203.md)

#### `mr_platEx(4011)` — 电话本搜索

```c
int32 mr_platEx (int32 code = 4011, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 搜索电话本。
**参数** input }T_MR_PHB_SEARCH_REQ;; input_len T_MR_PHB_SEARCH_REQ结构大小; output }T_MR_PHB_SEARCH_RSP;; output_len T_MR_PHB_SEARCH_RSP结构大小; cb 无
**返回** MR_PHB_NOT_READY /*电话本初始化中*/ / MR_PHB_NOT_FOUND / //2种情况，1：搜索参数为空；2：未找到 / MR_PHB_SUCCESS / //搜索成功
[全文](mr_platEx-4011.md)

#### `mr_platEx(4012)` — 电话本编辑

```c
int32 mr_platEx (int32 code = 4012, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 修改，修改，添加电话本条目。
**参数** input 注：当具体信息中的号码和名称为空的时候表示要删除index指向的那个条目; input_len T_MR_PHB_SET_ENTRY_REQ结构大小; output 无; output_len 无; cb 无
**返回** MR_PHB_SUCCESS：请求已经发出 / MR_PHB_ERROR / 请求发送失败 / 注：这个操作是一个异步的过程，操作的结构会通过mr_event的形式上送。 / 具体看最后的事件说明.
[全文](mr_platEx-4012.md)

#### `mr_platEx(4016)` — 获取条目信息

```c
int32 mr_platEx (int32 code = 4016, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得电话本中的指定一个条目的信息。
**参数** input 是相对于具体的存储位置而言的，不是在列表中的位置; input_len T_MR_PHB_GET_ENTRY_REQ结构大小; output }T_MR_PHB_GET_ENTRY_RSP;; output_len T_MR_PHB_GET_ENTRY_RSP大小; cb 无
**返回** MR_PHB_OUT_OF_INDEX：索引越界 / MR_PHB_SUCCESS / ：读取成功 / MR_PHB_NOT_READY /*电话本初始化中*/
[全文](mr_platEx-4016.md)

#### `mr_platEx(4021)` — 设置本机号码

```c
int32 mr_platEx (int32 code = 4021, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 添加本机号码记录.指的是 电话本的 MSISDN 区。（无实现）
**参数** input 输入参数的起始地址; input_len 输入参数大小（字节数）; output 输出参数的起始地址; output_len 输出参数大小（字节数）; cb 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
**备注** Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下： typedef void (*MR_PLAT_EX_CB)(uint8* output, int32 output_len); 若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
[全文](mr_platEx-4021.md)

#### `mr_platEx(4032)` — 获取电话本条数

```c
int32 mr_platEx (int32 code = 4032, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得电话本的条数。
**参数** input }T_MR_PHB_GET_COUNT_REQ;; input_len T_MR_PHB_GET_COUNT_REQ大小; output }T_MR_PHB_GET_COUNT_RSP;; output_len T_MR_PHB_GET_COUNT_RSP大小; cb 无
**返回** MR_PHB_SUCCESS / 获得记录成功 / MR_PHB_NOT_READY 电话本初始化中 / MR_PHB_NOT_SUPPORT / 输入参数错误
[全文](mr_platEx-4032.md)

#### `mr_platEx(4033)` — 获取电话本操作状态

```c
int32 mr_platEx (int32 code = 4033, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得电话本操作的状态。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_PHB_NOT_READY （1004）初始化中 / MR_PHB_READY / （1002）可以进行操作
[全文](mr_platEx-4033.md)

#### `mr_platEx(4041)` — 创建平台电话本浏览对象

```c
int32 mr_platEx (int32 code = 4041, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 创建平台的电话本浏览对像。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** MR_SUCCESS ：创建浏览对象成功 / MR_FAILED ：创建浏览对象失败 / MR_IGNORE / ：不支持该功能
[全文](mr_platEx-4041.md)

#### `mr_platEx(4042)` — 获得选中记录信息

```c
int32 mr_platEx (int32 code = 4042, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 获得选中的一个电话本记录的信息。
**参数** input 无; input_len 无; output T_MR_PHB_ENTRY 结构指针; output_len T_MR_PHB_ENTRY 结构大小; cb 无
**返回** MR_SUCCESS ：获得信息成功 / MR_FAILED ：获得信息失败 / MR_IGNORE / ：不支持该功能 / 注：选中还是返回的操作将由MR_LOCALUI_EVENT（10） / 事件传递给VM / 0：MR_LOCALUI_OK / （表示用户选择了一个文件） / 1：MR_LOCALUI_CANCEL（表示用户选择退出浏览这个功能）
**备注** 数据结构： #define MR_PHB_MAX_NAME (36*2) #define MR_PHB_MAX_NUMBER (48*2) #define MR_PHB_MAX_SEARCH_PATTERN (60*2) typedef struct { S8 name[MR_PHB_MAX_NAME]; S8 number[MR_PHB_MAX_NUMBER]; S8 homeNumber[MR_PHB_MAX_NUMBER]; S8 officeNumber[MR_PHB_MAX_NUMBER]; S8 faxNumber[MR_PHB_MAX_NUMBER]; S8 emailAddress[MR_PHB_MAX_NUMBER]; }T_MR_PHB_ENTRY;
[全文](mr_platEx-4042.md)

#### `mr_platEx(4043)` — 销毁电话本浏览对象

```c
int32 mr_platEx (int32 code = 4043, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```
**说明** 销毁电话本浏览对象。
**参数** input 无; input_len 无; output 无; output_len 无; cb 无
**返回** 成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
[全文](mr_platEx-4043.md)
