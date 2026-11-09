# SKYENGINE API 全量索引

共 288 页，由 `ref/sky`（CHM 解包文本）自动规范化生成，内容保真。

| 页面 | 原型 | 一句话说明 |
|---|---|---|
| [抽象移植接口](抽象移植接口.md) | `抽象移植接口 SkyEngine抽象接口是SkyEngine根据移植的需要以及不同手机软件平台的共性，向下抽象的一套需求接口函数，无论什么样的软硬件平台上，只要实现了这些接口函数，` |  |
| [code 定义](code-定义.md) | `mr_plat/mr_platEx 事件定义 旧版本中的CODE范围定义 在老的版本中扩展接口code遵循着一下的范围约束。 code 范围 说明 0-99 展讯平台 100-19` |  |
| [SKYENGINE 简介](SKYENGINE-简介.md) | `` |  |
| [mr_call](mr_call.md) | `void mr_call(char * pNumber)` | 拨打电话。 |
| [mr_close](mr_close.md) | `int32 mr_close(MR_FILE_HANDLE f)` | 关闭文件。 |
| [mr_closeNetwork](mr_closeNetwork.md) | `int32 mr_closeNetwork(void)` | 断开网络拨号。 |
| [mr_closeSocket](mr_closeSocket.md) | `int32 mr_closeSocket(int32 s)` | 关闭socket。 |
| [mr_connect](mr_connect.md) | `int32 mr_connect(int32 s, int32 ip, uint16 port, int32 type)` | 建立 socket 连接。 |
| [mr_connectWAP](mr_connectWAP.md) | `void mr_connectWAP(char* wap)` | 连接WAP。 |
| [mr_dialogCreate](mr_dialogCreate.md) | `int32 mr_dialogCreate(const char * title, const char * text, int32 type)` | 创建对话框。 |
| [mr_dialogRefresh](mr_dialogRefresh.md) | `int32 mr_dialogRefresh(int32 dialog, const char * title, const char * text, int32 type)` | 刷新对话框。 |
| [mr_dialogRelease](mr_dialogRelease.md) | `int32 mr_dialogRelease(int32 dialog)` | 释放对话框。 |
| [mr_drawBitmap](mr_drawBitmap.md) | `void mr_drawBitmap(uint16* bmp, int16 x, int16 y, uint16 w, uint16 h)` | 绘制BITMAP。 |
| [mr_editCreate](mr_editCreate.md) | `int32 mr_editCreate(const char * title, const char * text, int32 type, int32 max_size)` | 创建编辑框。 |
| [mr_editGetText](mr_editGetText.md) | `const char* mr_editGetText(int32 edit)` | 获取编辑框内容。 |
| [mr_editRelease](mr_editRelease.md) | `int32 mr_editRelease(int32 edit)` | 释放编辑框。 |
| [mr_event](mr_event.md) | `int32 mr_event(int16 type, int32 param1, int32 param2)` | 发送事件给虚拟机，在应用层将通过mrc_event接收到相应的消息。 |
| [mr_exit](mr_exit.md) | `int32 mr_exit(void)` | 退出应用。 |
| [mr_ferrno](mr_ferrno.md) | `int32 mr_ferrno(void)` | 返回错误信息。 |
| [mr_findGetNext](mr_findGetNext.md) | `int32 mr_findGetNext(MR_SEARCH_HANDLE search_handle, char* buffer, uint32 len)` | 取得一个目录搜索的结果。 |
| [mr_findStart](mr_findStart.md) | `MR_SEARCH_HANDLE mr_findStart(const char* name, char* buffer, uint32 len)` | 开始目录搜索。 |
| [mr_findStop](mr_findStop.md) | `int32 mr_findStop(MR_SEARCH_HANDLE search_handle)` | 结束目录查找。 |
| [mr_getCharBitmap](mr_getCharBitmap.md) | `const char *mr_getCharBitmap(uint16 ch, uint16 fontSize, int *width, int *height)` | 获取字符点整。 |
| [mr_getDatetime](mr_getDatetime.md) | `int32 mr_getDatetime(mr_datetime* datetime)` | 获取当前的日期。 |
| [mr_getHostByName](mr_getHostByName.md) | `int32 mr_getHostByName(const char *name, MR_GET_HOST_CB cb)` | 域名解析。 |
| [mr_getLen](mr_getLen.md) | `int32 mr_getLen(const char* filename)` | 取得文件长度。 |
| [mr_getNetworkID](mr_getNetworkID.md) | `int32 mr_getNetworkID(void)` | 获取网络ID。 |
| [mr_getScreenInfo](mr_getScreenInfo.md) | `int32 mr_getScreenInfo(mr_screeninfo * screeninfo)` | 获取屏幕信息。 |
| [mr_getTime](mr_getTime.md) | `uint32 mr_getTime(void)` | 获取毫秒时间。 |
| [mr_getUserInfo](mr_getUserInfo.md) | `int32 mr_getUserInfo(mr_userinfo* info)` | 获取手机相关信息。 |
| [mr_info](mr_info.md) | `int32 mr_info(const char* filename)` | 获取文件属性。 |
| [mr_initNetwork](mr_initNetwork.md) | `int32 mr_initNetwork(MR_INIT_NETWORK_CB cb, const char *mode)` | 网络初始化。 |
| [mr_mem_free](mr_mem_free.md) | `int32 mr_mem_free (char* mem, uint32 mem_len)` | 内存释放接口。 |
| [mr_mem_get](mr_mem_get.md) | `int32 mr_mem_get (char** mem_base, uint32* mem_len)` | 内存申请函数。 |
| [mr_menuCreate](mr_menuCreate.md) | `int32 mr_menuCreate(const char * title, int16 num)` | 创建菜单。 |
| [mr_menuRefresh](mr_menuRefresh.md) | `int32 mr_menuRefresh(int32 menu)` | 刷新菜单。 |
| [mr_menuRelease](mr_menuRelease.md) | `int32 mr_menuRelease(int32 menu)` | 释放菜单。 |
| [mr_menuSetItem](mr_menuSetItem.md) | `int32 mr_menuSetItem(int32 menu, const char *text, int32 index)` | 设置菜单项。 |
| [mr_menuShow](mr_menuShow.md) | `int32 mr_menuShow(int32 menu)` | 显示菜单。 |
| [mr_mkDir](mr_mkDir.md) | `int32 mr_mkDir(const char* name)` | 创建目录。 |
| [mr_newSIMInd](mr_newSIMInd.md) | `int32 mr_newSIMInd(int16 type, uint8* old_IMSI)` | 用户SIM卡变更通知。 |
| [mr_open](mr_open.md) | `MR_FILE_HANDLE mr_open(const char* filename, uint32 mode)` | 打开文件。 |
| [mr_pauseApp](mr_pauseApp.md) | `int32 mr_pauseApp(void)` | 暂停虚拟机。 |
| [mr_plat(1)](mr_plat-1.md) | `int32 mr_plat(int32 code = 1, int32 param)` | 调节cpu频率。 |
| [mr_plat(1001)](mr_plat-1001.md) | `int32 mr_plat(int32 code = 1001, int32 param)` | 异步connect状态查询。 |
| [mr_plat(1002)](mr_plat-1002.md) | `int32 mr_plat(int32 code = 1002, int32 param)` | 设置socketconnect等待时间“废止“。 |
| [mr_plat(1003)](mr_plat-1003.md) | `int32 mr_plat(int32 code = 1003, int32 param)` | 将后台程序切换到前台运行。 |
| [mr_plat(1004)](mr_plat-1004.md) | `int32 mr_plat(int32 code = 1004, int32 param)` | 多sim卡待机时设置所用sim卡。 |
| [mr_plat(1006)](mr_plat-1006.md) | `int32 mr_plat(int32 code = 1006, int32 param)` | 停止在idle上显示图标或者idle背景。 |
| [mr_plat(101)](mr_plat-101.md) | `int32 mr_plat(int32 code = 101, int32 param)` | 设置图象旋转显示的角度。 |
| [mr_plat(1011)](mr_plat-1011.md) | `int32 mr_plat(int32 code = 1011, int32 param)` | 设置收到新短信的时候是否显示提示界面。 |
| [mr_plat(1016) -初始化](mr_plat-1016.md) | `int32 mr_plat(int32 code = 1016, int32 param)` | 初始化信号强度。 |
| [mr_plat(1018)](mr_plat-1018.md) | `int32 mr_plat(int32 code = 1018, int32 param)` | 关闭获得信号强度功能。 |
| [mr_plat(102)](mr_plat-102.md) | `int32 mr_plat(int32 code = 102, int32 param)` | 告知驱动PCM写入数据的绝对地址。（再根据数据的其实地址可以算出等待播放的数据量） |
| [mr_plat(1020)](mr_plat-1020.md) | `int32 mr_plat(int32 code = 1020, int32 param)` | 获得当前背光状态x18x。 |
| [mr_plat(103)](mr_plat-103.md) | `int32 mr_plat(int32 code = 103, int32 param)` | 取得PCM数据已经播放掉的数据的绝对地址。 |
| [mr_plat(104)](mr_plat-104.md) | `int32 mr_plat(int32 code = 104, int32 param)` | 销毁窗口而不画屏幕。（BASE WIN以上的窗口都销毁）。 |
| [mr_plat(105)](mr_plat-105.md) | `int32 mr_plat(int32 code = 105, int32 param)` | 获取旋转角度。（未实现） |
| [mr_plat(1100)](mr_plat-1100.md) | `int32 mr_plat(int32 code = 1100, int32 param)` | 获得短信操作的状态。 |
| [mr_plat(1101)](mr_plat-1101.md) | `int32 mr_plat(int32 code = 1101, int32 param)` | 获得短信信箱中短息的条数。 |
| [mr_plat(1105)](mr_plat-1105.md) | `int32 mr_plat(int32 code = 1105, int32 param)` | 发送获得手机和sim卡存储空间的容量的请求。 |
| [mr_plat(1106)](mr_plat-1106.md) | `int32 mr_plat(int32 code = 1106, int32 param)` | 发送获得短信中心的号码的请求。 |
| [mr_plat(1107)](mr_plat-1107.md) | `int32 mr_plat(int32 code = 1107, int32 param)` | 发送获得apn信息的请求。 |
| [mr_plat(1110)](mr_plat-1110.md) | `int32 mr_plat(int32 code = 1110, int32 param)` | 设置apn使用的标志位。 |
| [mr_plat(1111)](mr_plat-1111.md) | `int32 mr_plat(int32 code = 1111, int32 param)` | 调用mtk的界面设置apn。 |
| [mr_plat(1113)](mr_plat-1113.md) | `int32 mr_plat(int32 code = 1113, int32 param)` | 还原手机主题。 |
| [mr_plat(1114)](mr_plat-1114.md) | `int32 mr_plat(int32 code = 1114, int32 param)` | 获得当前激活的主题的app id。 |
| [mr_plat(1115)](mr_plat-1115.md) | `int32 mr_plat(int32 code = 1115, int32 param)` | 设置主题中主菜单当前选中的宫格的index。 |
| [mr_plat(1205)](mr_plat-1205.md) | `int32 mr_plat(int32 code = 1205, int32 param)` | 获取手机是否是触摸屏信息。 |
| [mr_plat(1206)](mr_plat-1206.md) | `int32 mr_plat(int32 code = 1206, int32 param)` | 获取手机当前设置的语言。 |
| [mr_plat(1211)](mr_plat-1211.md) | `int32 mr_plat(int32 code = 1221, int32 param)` | 调用平台接口产生随即数。 |
| [mr_plat(1213)](mr_plat-1213.md) | `int32 mr_plat(int32 code = 1213, int32 param)` | 获得手机当前的情景模式。 |
| [mr_plat(1214)](mr_plat-1214.md) | `int32 mr_plat(int32 code = 1214, int32 param)` | 屏幕该界面下按挂机键回idle的功能。 |
| [mr_plat(1215)](mr_plat-1215.md) | `int32 mr_plat(int32 code = 1215, int32 param)` | 获得cell id的初始化。 |
| [mr_plat(1216)](mr_plat-1216.md) | `int32 mr_plat(int32 code = 1216, int32 param)` | 关闭获得cell id功能。 |
| [mr_plat(1217)](mr_plat-1217.md) | `int32 mr_plat(int32 code = 1217, int32 param)` | 退出天气预报。 |
| [mr_plat(1218)](mr_plat-1218.md) | `int32 mr_plat(int32 code = 1218, int32 param)` | 查询存储卡的状态。 |
| [mr_plat(1231)](mr_plat-1231.md) | `int32 mr_plat(int32 code = 1231, int32 param)` | 获得当前文件的指针的位置。 |
| [mr_plat(1302)](mr_plat-1302.md) | `int32 mr_plat(int32 code = 1302, int32 param)` | 设置声音的大小。（播放时候的大小，非情景模式中的设置）。 |
| [mr_plat(1310)](mr_plat-1310.md) | `int32 mr_plat(int32 code = 1310, int32 param)` | 释放层。 |
| [mr_plat(1312)](mr_plat-1312.md) | `int32 mr_plat(int32 code = 1312, int32 param)` | 设置激活层。 |
| [mr_plat(1314)](mr_plat-1314.md) | `int32 mr_plat(int32 code = 1314, int32 param)` | 设置png的背景层。 |
| [mr_plat(1317)](mr_plat-1317.md) | `int32 mr_plat(int32 code = 1317, int32 param)` | 设置层的透明值。 |
| [mr_plat(1318)](mr_plat-1318.md) | `int32 mr_plat(int32 code = 1318, int32 param)` | 关闭层的透明属性。 |
| [mr_plat(1319)](mr_plat-1319.md) | `int32 mr_plat(int32 code = 1319, int32 param)` | 设置层的透明色（透明色是纯蓝色）。 |
| [mr_plat(1320)](mr_plat-1320.md) | `int32 mr_plat(int32 code = 1320, int32 param)` | 关闭层的透明色处理。 |
| [mr_plat(1321)](mr_plat-1321.md) | `int32 mr_plat(int32 code = 1321, int32 param)` | 设置刷屏锁后，之后的刷屏动作都无效 |
| [mr_plat(1322)](mr_plat-1322.md) | `int32 mr_plat(int32 code = 1322, int32 param)` | 需要在调用刷屏锁之后匹配调用 。 |
| [mr_plat(1325)](mr_plat-1325.md) | `int32 mr_plat(int32 code = 1325, int32 param)` | 绘制主菜单的背景（直接绘制的当前激活层上）。 |
| [mr_plat(1326)](mr_plat-1326.md) | `int32 mr_plat(int32 code = 1326, int32 param)` | 控制状态条是否显示。 |
| [mr_plat(1327)](mr_plat-1327.md) | `int32 mr_plat(int32 code = 1327, int32 param)` | 查询WIFI是否可用，这里的可用是只已经连上热点。 |
| [mr_plat(1328)](mr_plat-1328.md) | `int32 mr_plat(int32 code = 1328, int32 param)` | 设置是否使用WIFI联网。 |
| [mr_plat(1333)](mr_plat-1333.md) | `int32 mr_plat(int32 code = 1333, int32 param)` | 进入TODO LIST。 |
| [mr_plat(1391)](mr_plat-1391.md) | `int32 mr_plat(int32 code = 1391, int32 param)` | 查询移植层是否支持后台运行接口。 |
| [mr_plat(2)](mr_plat-2.md) | `int32 mr_plat(int32 code = 2, int32 param)` | 获取平台可映射虚拟键数目。 |
| [mr_plat(2500)](mr_plat-2500.md) | `int32 mr_plat(int32 code = 2500, int32 param)` | 初始化camera。Parameters |
| [mr_plat(2502)](mr_plat-2502.md) | `int32 mr_plat(int32 code = 2502, int32 param)` | 暂停camera。 |
| [mr_plat(2503)](mr_plat-2503.md) | `int32 mr_plat(int32 code = 2503, int32 param)` | 恢复camera到preview状态。 |
| [mr_plat(2504)](mr_plat-2504.md) | `int32 mr_plat(int32 code = 2504, int32 param)` | 关闭camera。 |
| [mr_plat(2506)](mr_plat-2506.md) | `int32 mr_plat(int32 code = 2506, int32 param)` | 获得camera的缩放等级。 |
| [mr_plat(2507)](mr_plat-2507.md) | `int32 mr_plat(int32 code = 2507, int32 param)` | camera 放大。 |
| [mr_plat(2508)](mr_plat-2508.md) | `int32 mr_plat(int32 code = 2508, int32 param)` | camera 缩小。 |
| [mr_plat(2701)](mr_plat-2701.md) | `int32 mr_plat(int32 code = 2701, int32 param)` | 录音暂停。 |
| [mr_plat(2702)](mr_plat-2702.md) | `int32 mr_plat(int32 code = 2702, int32 param)` | 录音恢复。 |
| [mr_plat(2703)](mr_plat-2703.md) | `int32 mr_plat(int32 code = 2703, int32 param)` | 录音停止。 |
| [mr_plat(3)](mr_plat-3.md) | `int32 mr_plat(int32 code = 3, int32 param)` | 获取虚拟键对应的按下、弹起状态。 |
| [mr_plat(3012)](mr_plat-3012.md) | `int32 mr_plat(int32 code = 3012, int32 param)` | 动画停止。 |
| [mr_plat(4)](mr_plat-4.md) | `int32 mr_plat(int32 code = 4, int32 param)` | nes特殊操作。 |
| [mr_plat(4001)](mr_plat-4001.md) | `int32 mr_plat(int32 code = 4001, int32 param)` | 停止动感芯片监听。 |
| [mr_plat(4002)](mr_plat-4002.md) | `int32 mr_plat(int32 code = 4002, int32 param)` | 给动感芯片上电。 |
| [mr_plat(4003)](mr_plat-4003.md) | `int32 mr_plat(int32 code = 4003, int32 param)` | 给动感芯片断电。 |
| [mr_plat(4004)](mr_plat-4004.md) | `int32 mr_plat(int32 code = 4004, int32 param)` | 动感芯片监听晃动模式。 |
| [mr_plat(4005)](mr_plat-4005.md) | `int32 mr_plat(int32 code = 4005, int32 param)` | 设置动感芯片监听倾斜模式。 |
| [mr_plat(4006)](mr_plat-4006.md) | `int32 mr_plat(int32 code = 4006, int32 param)` | 获取动感芯片上送的数值的范围值 。 |
| [mr_plat(4017)](mr_plat-4017.md) | `int32 mr_plat(int32 code = 4017, int32 param)` | 拷贝一条记录。（没实现） |
| [mr_plat(4022)](mr_plat-4022.md) | `int32 mr_plat(int32 code = 4022, int32 param)` | 获得本机号码。（无实现） |
| [mr_plat(4031)](mr_plat-4031.md) | `int32 mr_plat(int32 code = 4031, int32 param)` | 删除所有记录。（无实现） |
| [mr_plat(5)](mr_plat-5.md) | `int32 mr_plat(int32 code = 5, int32 param)` | 保存模拟器游戏积分（覆盖式保存）。 |
| [mr_plat(6)](mr_plat-6.md) | `int32 mr_plat(int32 code = 6, int32 param)` | 读取模拟器游戏积分。 |
| [mr_plat(7)](mr_plat-7.md) | `int32 mr_plat(int32 code = 7, int32 param)` | 按键音开启关闭控制。 |
| [mr_plat(8)](mr_plat-8.md) | `int32 mr_plat(int32 code = 8, int32 param)` | 设置wap下载的.nes保存所使用的存储器。 |
| [mr_plat](mr_plat.md) | `int32 mr_plat(int32 code, int32 param)` | 基本的平台调用接口，对应于应用层的mrc_plat接口。 |
| [mr_platEx(0x90001)](mr_platEx-0x90001.md) | `int32 mr_platEx (int32 code = 0x90001, uint8* input, int32 input_len, uint8** output, int3` | 获取当前时区信息。 |
| [mr_platEx(0x90002)](mr_platEx-0x90002.md) | `int32 mr_platEx (int32 code = 0x90002, uint8* input, int32 input_len, uint8** output, int3` | 获取手机支持的全部语言。 |
| [mr_platEx(1)](mr_platEx-1.md) | `int32 mr_platEx (int32 code = 1, uint8* input, int32 input_len, uint8** output, int32* out` | 建一个单/多选list。 |
| [mr_platEx(1001)](mr_platEx-1001.md) | `int32 mr_platEx (int32 code = 1001, uint8* input, int32 input_len, uint8** output, int32* ` | 第二内存申请。在某些内存紧张的平台中，sky |
| [mr_platEx(1002)](mr_platEx-1002.md) | `int32 mr_platEx (int32 code = 1002, uint8* input, int32 input_len, uint8** output, int32* ` | 释放申请到的第二内存。 |
| [mr_platEx(1003)](mr_platEx-1003.md) | `int32 mr_platEx (int32 code = 1003, uint8* input, int32 input_len, uint8** output, int32* ` | 绑定一个socket到本机端口（udp）。 |
| [mr_platEx(1004)](mr_platEx-1004.md) | `int32 mr_platEx (int32 code = 1004, uint8* input, int32 input_len, uint8** output, int32* ` | 后台运行。 |
| [mr_platEx(1005)](mr_platEx-1005.md) | `int32 mr_platEx (int32 code = 1005, uint8* input, int32 input_len, uint8** output, int32* ` | 显示一张图片。 |
| [mr_platEx(1006)](mr_platEx-1006.md) | `int32 mr_platEx (int32 code = 1006, uint8* input, int32 input_len, uint8** output, int32* ` | 启动平台QQ。 |
| [mr_platEx(1008)](mr_platEx-1008.md) | `int32 mr_platEx (int32 code = 1008, uint8* input, int32 input_len, uint8** output, int32* ` | 调用mtk的发送短信界面。 |
| [mr_platEx(1009)](mr_platEx-1009.md) | `int32 mr_platEx (int32 code = 1009, uint8* input, int32 input_len, uint8** output, int32* ` | 设置墙纸。 |
| [mr_platEx(1012)](mr_platEx-1012.md) | `int32 mr_platEx (int32 code = 1012, uint8* input, int32 input_len, uint8** output, int32* ` | 申请内部cache。 |
| [mr_platEx(1013)](mr_platEx-1013.md) | `int32 mr_platEx (int32 code = 1013, uint8* input, int32 input_len, uint8** output, int32* ` | 释放申请内部cache。 |
| [mr_platEx(1014)](mr_platEx-1014.md) | `int32 mr_platEx (int32 code = 1014, uint8* input, int32 input_len, uint8** output, int32* ` | 申请扩展内存。 |
| [mr_platEx(1015)](mr_platEx-1015.md) | `int32 mr_platEx (int32 code = 1015, uint8* input, int32 input_len, uint8** output, int32* ` | 释放扩展内存。 |
| [mr_platEx(1017)](mr_platEx-1017.md) | `int32 mr_platEx (int32 code = 1017, uint8* input, int32 input_len, uint8** output, int32* ` | 获得信号强度。 |
| [mr_platEx(11)](mr_platEx-11.md) | `int32 mr_platEx (int32 code = 11, uint8* input, int32 input_len, uint8** output, int32* ou` | 获取手机平台的mp3存储目录名称。 |
| [mr_platEx(1102)](mr_platEx-1102.md) | `int32 mr_platEx (int32 code = 1102, uint8* input, int32 input_len, uint8** output, int32* ` | 获得指定一条短信的信息。 |
| [mr_platEx(1103)](mr_platEx-1103.md) | `int32 mr_platEx (int32 code = 1103, uint8* input, int32 input_len, uint8** output, int32* ` | 读取一条短信。 |
| [mr_platEx(1104)](mr_platEx-1104.md) | `int32 mr_platEx (int32 code = 1104, uint8* input, int32 input_len, uint8** output, int32* ` | 删除一条短信。 |
| [mr_platEx(1108)](mr_platEx-1108.md) | `int32 mr_platEx (int32 code = 1108, uint8* input, int32 input_len, uint8** output, int32* ` | 从缓存中读取apn信息。 |
| [mr_platEx(1109)](mr_platEx-1109.md) | `int32 mr_platEx (int32 code = 1109, uint8* input, int32 input_len, uint8** output, int32* ` | 设置apn信息。 |
| [mr_platEx(1112)](mr_platEx-1112.md) | `int32 mr_platEx (int32 code = 1112, uint8* input, int32 input_len, uint8** output, int32* ` | 激活手机主题。 |
| [mr_platEx(1116)](mr_platEx-1116.md) | `int32 mr_platEx (int32 code = 1116, uint8* input, int32 input_len, uint8** output, int32* ` | 获取编译时间。 |
| [mr_platEx(1117)](mr_platEx-1117.md) | `int32 mr_platEx (int32 code = 1117, uint8* input, int32 input_len, uint8** output, int32* ` | 获取硬件版本号。 |
| [mr_platEx(12)](mr_platEx-12.md) | `int32 mr_platEx (int32 code = 12, uint8* input, int32 input_len, uint8** output, int32* ou` | 获取手机平台的picture存储目录名称。 |
| [mr_platEx(1201)](mr_platEx-1201.md) | `int32 mr_platEx (int32 code = 1201, uint8* input, int32 input_len, uint8** output, int32* ` | 获取字宽字高。这个接口主要为了解决某些平台字宽字高不等的情况。这个接口返回在该平台上最大的字宽和字高。 |
| [mr_platEx(1203)](mr_platEx-1203.md) | `int32 mr_platEx (int32 code = 1203, uint8* input, int32 input_len, uint8** output, int32* ` | 调用发送彩信功能。 |
| [mr_platEx(1204)](mr_platEx-1204.md) | `int32 mr_platEx (int32 code = 1204, uint8* input, int32 input_len, uint8** output, int32* ` | 切换目录。 |
| [mr_platEx(1207)](mr_platEx-1207.md) | `int32 mr_platEx (int32 code = 1207, uint8* input, int32 input_len, uint8** output, int32* ` | unicode转gb。 |
| [mr_platEx(1208)](mr_platEx-1208.md) | `int32 mr_platEx (int32 code = 1208, uint8* input, int32 input_len, uint8** output, int32* ` | 设置手机铃声。 |
| [mr_platEx(1210)](mr_platEx-1210.md) | `int32 mr_platEx (int32 code = 1210, uint8* input, int32 input_len, uint8** output, int32* ` | 获取NES模拟器按键布局。 |
| [mr_platEx(1220)](mr_platEx-1220.md) | `int32 mr_platEx (int32 code = 1220, uint8* input, int32 input_len, uint8** output, int32* ` | 获得rom目录。 |
| [mr_platEx(1221)](mr_platEx-1221.md) | `int32 mr_platEx (int32 code = 1221, uint8* input, int32 input_len, uint8** output, int32* ` | 获得applist title 名称。 |
| [mr_platEx(1222)](mr_platEx-1222.md) | `int32 mr_platEx (int32 code = 1222, uint8* input, int32 input_len, uint8** output, int32* ` | 设置lcd一直为开，lcd 不进入sleep。 |
| [mr_platEx(1223)](mr_platEx-1223.md) | `int32 mr_platEx (int32 code = 1223, uint8* input, int32 input_len, uint8** output, int32* ` | 恢复lcd 设置，lcd 可定时进入sleep。 |
| [mr_platEx(1224)](mr_platEx-1224.md) | `int32 mr_platEx (int32 code = 1224, uint8* input, int32 input_len, uint8** output, int32* ` | 获取小区ID等部分信息。 |
| [mr_platEx(1225)](mr_platEx-1225.md) | `int32 mr_platEx (int32 code = 1225, uint8* input, int32 input_len, uint8** output, int32* ` | 获取手柄信息。 |
| [mr_platEx(1226)](mr_platEx-1226.md) | `int32 mr_platEx (int32 code = 1226, uint8* input, int32 input_len, uint8** output, int32* ` | 获得当前网络的id。 |
| [mr_platEx(1305)](mr_platEx-1305.md) | `int32 mr_platEx (int32 code = 1305, uint8* input, int32 input_len, uint8** output, int32* ` | 获得指定盘符的剩余空间大小。 |
| [mr_platEx(1306)](mr_platEx-1306.md) | `int32 mr_platEx (int32 code = 1306, uint8* input, int32 input_len, uint8** output, int32* ` | 用来获取厂商自己设置的A、B、C、D、等存储设备的名称，例如：B设备名字为“U盘”,如果查询的设备不存在则返回MR_FAILED。（展讯接口 |
| [mr_platEx(1307)](mr_platEx-1307.md) | `int32 mr_platEx (int32 code = 1307, uint8* input, int32 input_len, uint8** output, int32* ` | 获得sim卡个数等信息。 |
| [mr_platEx(1308)](mr_platEx-1308.md) | `int32 mr_platEx (int32 code = 1308, uint8* input, int32 input_len, uint8** output, int32* ` | 设置参与刷新的层的句柄的列表。 |
| [mr_platEx(1309)](mr_platEx-1309.md) | `int32 mr_platEx (int32 code = 1309, uint8* input, int32 input_len, uint8** output, int32* ` | 创建层。 |
| [mr_platEx(1311)](mr_platEx-1311.md) | `int32 mr_platEx (int32 code = 1311, uint8* input, int32 input_len, uint8** output, int32* ` | 获得base层的句柄。 |
| [mr_platEx(1313)](mr_platEx-1313.md) | `int32 mr_platEx (int32 code = 1313, uint8* input, int32 input_len, uint8** output, int32* ` | 设置层位置。 |
| [mr_platEx(1315)](mr_platEx-1315.md) | `int32 mr_platEx (int32 code = 1315, uint8* input, int32 input_len, uint8** output, int32* ` | 获取激活层信息。 |
| [mr_platEx(1316)](mr_platEx-1316.md) | `int32 mr_platEx (int32 code = 1316, uint8* input, int32 input_len, uint8** output, int32* ` | 进行层叠加。 |
| [mr_platEx(1323)](mr_platEx-1323.md) | `int32 mr_platEx (int32 code = 1323, uint8* input, int32 input_len, uint8** output, int32* ` | 设置异步转后台。 |
| [mr_platEx(1332) -SKYQQ接口](mr_platEx-1332.md) | `int32 mr_platEx (int32 code = 1332, uint8* input, int32 input_len, uint8** output, int32* ` | SKYQQ接口。 |
| [mr_platEx(1401)](mr_platEx-1401.md) | `int32 mr_platEx (int32 code = 1401, uint8* input, int32 input_len, uint8** output, int32* ` | 初始化筛选器。 |
| [mr_platEx(1402)](mr_platEx-1402.md) | `int32 mr_platEx (int32 code = 1402, uint8* input, int32 input_len, uint8** output, int32* ` | 设置要显示的文件类型（要浏览一类文件需要多次调用这个接口）。 |
| [mr_platEx(1403)](mr_platEx-1403.md) | `int32 mr_platEx (int32 code = 1403, uint8* input, int32 input_len, uint8** output, int32* ` | 设置不要显示的文件类型。 |
| [mr_platEx(1404)](mr_platEx-1404.md) | `int32 mr_platEx (int32 code = 1404, uint8* input, int32 input_len, uint8** output, int32* ` | 创建浏览，调用平台本地浏览界面。 |
| [mr_platEx(1405)](mr_platEx-1405.md) | `int32 mr_platEx (int32 code = 1405, uint8* input, int32 input_len, uint8** output, int32* ` | 获得通过浏览器选中的文件的绝对路径。 |
| [mr_platEx(1406)](mr_platEx-1406.md) | `int32 mr_platEx (int32 code = 1406, uint8* input, int32 input_len, uint8** output, int32* ` | 销毁浏览器对象。 |
| [mr_platEx(2)](mr_platEx-2.md) | `int32 mr_platEx (int32 code = 2, uint8* input, int32 input_len, uint8** output, int32* out` | 设置菜单项。 |
| [mr_platEx(201x)](mr_platEx-201x.md) | `int32 mr_platEx (int32 code = 201x, uint8* input, int32 input_len, uint8** output, int32* ` | 设备初始化。 |
| [mr_platEx(202x)](mr_platEx-202x.md) | `int32 mr_platEx (int32 code = 202x, uint8* input, int32 input_len, uint8** output, int32* ` | 加载一个文件。 |
| [mr_platEx(203x)](mr_platEx-203x.md) | `int32 mr_platEx (int32 code = 203x, uint8* input, int32 input_len, uint8** output, int32* ` | 加载缓冲数据。 |
| [mr_platEx(204x)](mr_platEx-204x.md) | `int32 mr_platEx (int32 code = 204x, uint8* input, int32 input_len, uint8** output, int32* ` | 从当前的位置开始播放。 |
| [mr_platEx(205x)](mr_platEx-205x.md) | `int32 mr_platEx (int32 code = 205x, uint8* input, int32 input_len, uint8** output, int32* ` | 暂停播放。 |
| [mr_platEx(206x)](mr_platEx-206x.md) | `int32 mr_platEx (int32 code = 206x, uint8* input, int32 input_len, uint8** output, int32* ` | 继续播放。 |
| [mr_platEx(207x)](mr_platEx-207x.md) | `int32 mr_platEx (int32 code = 207x, uint8* input, int32 input_len, uint8** output, int32* ` | 停止播放。 |
| [mr_platEx(208x)](mr_platEx-208x.md) | `int32 mr_platEx (int32 code = 208x, uint8* input, int32 input_len, uint8** output, int32* ` | 关闭设备。 |
| [mr_platEx(209x)](mr_platEx-209x.md) | `int32 mr_platEx (int32 code = 209x, uint8* input, int32 input_len, uint8** output, int32* ` | 获取当前设备的状态。 |
| [mr_platEx(210x)](mr_platEx-210x.md) | `int32 mr_platEx (int32 code = 210x, uint8* input, int32 input_len, uint8** output, int32* ` | 设置播放位置，已经播放了多少时间。 |
| [mr_platEx(211x)](mr_platEx-211x.md) | `int32 mr_platEx (int32 code = 211x, uint8* input, int32 input_len, uint8** output, int32* ` | 设置播放位置，已经播放了相对文件或者缓冲的起始位置的偏移量。 |
| [mr_platEx(212x)](mr_platEx-212x.md) | `int32 mr_platEx (int32 code = 212x, uint8* input, int32 input_len, uint8** output, int32* ` | 获取整首歌的播放时间。 |
| [mr_platEx(213x)](mr_platEx-213x.md) | `int32 mr_platEx (int32 code = 213x, uint8* input, int32 input_len, uint8** output, int32* ` | 获取当前的播放进度时间。 |
| [mr_platEx(215x)](mr_platEx-215x.md) | `int32 mr_platEx (int32 code = 215x, uint8* input, int32 input_len, uint8** output, int32* ` | 获取当前的播放进度时间。 |
| [mr_platEx(216x)](mr_platEx-216x.md) | `int32 mr_platEx (int32 code = 216x, uint8* input, int32 input_len, uint8** output, int32* ` | 多媒体模块释放。 |
| [mr_platEx(220x)](mr_platEx-220x.md) | `int32 mr_platEx (int32 code = 220x, uint8* input, int32 input_len, uint8** output, int32* ` | 占用IRAM。 |
| [mr_platEx(221x)](mr_platEx-221x.md) | `int32 mr_platEx (int32 code = 221x, uint8* input, int32 input_len, uint8** output, int32* ` | 释放IRAM。 |
| [mr_platEx(222x)](mr_platEx-222x.md) | `int32 mr_platEx (int32 code = 222x, uint8* input, int32 input_len, uint8** output, int32* ` | 多通道加载。加载一个用于多通道的数据，目前只支持wav和midi 。 |
| [mr_platEx(223x)](mr_platEx-223x.md) | `int32 mr_platEx (int32 code = 223x, uint8* input, int32 input_len, uint8** output, int32* ` | 播放已经加载的数据。 |
| [mr_platEx(224x)](mr_platEx-224x.md) | `int32 mr_platEx (int32 code = 224x, uint8* input, int32 input_len, uint8** output, int32* ` | 停止播放。 |
| [mr_platEx(225x)](mr_platEx-225x.md) | `int32 mr_platEx (int32 code = 225x, uint8* input, int32 input_len, uint8** output, int32* ` | 释放已经加载的数据。 |
| [mr_platEx(2501)](mr_platEx-2501.md) | `int32 mr_platEx (int32 code = 2501, uint8* input, int32 input_len, uint8** output, int32* ` | 启动camera，进入preview状态。 |
| [mr_platEx(2505)](mr_platEx-2505.md) | `int32 mr_platEx (int32 code = 2505, uint8* input, int32 input_len, uint8** output, int32* ` | 拍照。 |
| [mr_platEx(2509)](mr_platEx-2509.md) | `int32 mr_platEx (int32 code = 2509, uint8* input, int32 input_len, uint8** output, int32* ` | 获取预览数据。一旦调用该接口，则会获取预览数据，即使关闭了camera，任然在获取当前激活层的数据。 |
| [mr_platEx(2700)](mr_platEx-2700.md) | `int32 mr_platEx (int32 code = 2700, uint8* input, int32 input_len, uint8** output, int32* ` | 开始录音。 |
| [mr_platEx(2704)](mr_platEx-2704.md) | `int32 mr_platEx (int32 code = 2704, uint8* input, int32 input_len, uint8** output, int32* ` | 在录音启动的接口中将格式设置成pcm，src_type设置为SRC_STREAM的情况下，调用本接口来获得pcm数据 |
| [mr_platEx(3)](mr_platEx-3.md) | `int32 mr_platEx (int32 code = 3, uint8* input, int32 input_len, uint8** output, int32* out` | MR_LIST_CREATE_POP。 |
| [mr_platEx(3001)](mr_platEx-3001.md) | `int32 mr_platEx (int32 code = 3001, uint8* input, int32 input_len, uint8** output, int32* ` | 获取图片信息。 |
| [mr_platEx(3002)](mr_platEx-3002.md) | `int32 mr_platEx (int32 code = 3002, uint8* input, int32 input_len, uint8** output, int32* ` | 解码一张图片，将解完的数据放到dest所指的buf中，并通知vm解码结果。（gif不在此中处理）。 |
| [mr_platEx(3003)](mr_platEx-3003.md) | `int32 mr_platEx (int32 code = 3003, uint8* input, int32 input_len, uint8** output, int32* ` | 取得图像解码状态（异步解码）。未实现。 |
| [mr_platEx(3004)](mr_platEx-3004.md) | `int32 mr_platEx (int32 code = 3004, uint8* input, int32 input_len, uint8** output, int32* ` | 解码一张GIF图片，将解完的数据放到dest所指的buf中，并通知vm解码结果。 |
| [mr_platEx(3005)](mr_platEx-3005.md) | `int32 mr_platEx (int32 code = 3005, uint8* input, int32 input_len, uint8** output, int32* ` | 应用通知移植层释放先前gif解码（mr_platEx（3004））用到的资源。 |
| [mr_platEx(3007)](mr_platEx-3007.md) | `int32 mr_platEx (int32 code = 3007, uint8* input, int32 input_len, uint8** output, int32* ` | 绘制BUFFER。 |
| [mr_platEx(3008)](mr_platEx-3008.md) | `int32 mr_platEx (int32 code = 3008, uint8* input, int32 input_len, uint8** output, int32* ` | 获取active layer。 |
| [mr_platEx(3009)](mr_platEx-3009.md) | `int32 mr_platEx (int32 code = 3009, uint8* input, int32 input_len, uint8** output, int32* ` | 直接刷屏（非阻塞形式)。 |
| [mr_platEx(3010)](mr_platEx-3010.md) | `int32 mr_platEx (int32 code = 3010, uint8* input, int32 input_len, uint8** output, int32* ` | 直接调用平台接口将图片绘制到指定的矩形内。 |
| [mr_platEx(3011)](mr_platEx-3011.md) | `int32 mr_platEx (int32 code = 3011, uint8* input, int32 input_len, uint8** output, int32* ` | 显示gif动画的接口（直接绘制到frame |
| [mr_platEx(3013)](mr_platEx-3013.md) | `int32 mr_platEx (int32 code = 3013, uint8* input, int32 input_len, uint8** output, int32* ` | MR_SET_ANIMATION_BLT_CB，未实现。 |
| [mr_platEx(3014)](mr_platEx-3014.md) | `int32 mr_platEx (int32 code = 3014, uint8* input, int32 input_len, uint8** output, int32* ` | 绘制mtk资源格式的图片。 |
| [mr_platEx(3015)](mr_platEx-3015.md) | `int32 mr_platEx (int32 code = 3015, uint8* input, int32 input_len, uint8** output, int32* ` | 绘制mtk资源格式的gif动画。动画停止需要调用mr_plat(3012,句柄)。 |
| [mr_platEx(4)](mr_platEx-4.md) | `int32 mr_platEx (int32 code = 4, uint8* input, int32 input_len, uint8** output, int32* out` | MR_LIST_SET_ITEM_POP。 |
| [mr_platEx(4011)](mr_platEx-4011.md) | `int32 mr_platEx (int32 code = 4011, uint8* input, int32 input_len, uint8** output, int32* ` | 搜索电话本。 |
| [mr_platEx(4012)](mr_platEx-4012.md) | `int32 mr_platEx (int32 code = 4012, uint8* input, int32 input_len, uint8** output, int32* ` | 修改，修改，添加电话本条目。 |
| [mr_platEx(4016)](mr_platEx-4016.md) | `int32 mr_platEx (int32 code = 4016, uint8* input, int32 input_len, uint8** output, int32* ` | 获得电话本中的指定一个条目的信息。 |
| [mr_platEx(4021)](mr_platEx-4021.md) | `int32 mr_platEx (int32 code = 4021, uint8* input, int32 input_len, uint8** output, int32* ` | 添加本机号码记录.指的是 电话本的 MSISDN 区。（无实现） |
| [mr_platEx(4032)](mr_platEx-4032.md) | `int32 mr_platEx (int32 code = 4032, uint8* input, int32 input_len, uint8** output, int32* ` | 获得电话本的条数。 |
| [mr_platEx(4033)](mr_platEx-4033.md) | `int32 mr_platEx (int32 code = 4033, uint8* input, int32 input_len, uint8** output, int32* ` | 获得电话本操作的状态。 |
| [mr_platEx(4041)](mr_platEx-4041.md) | `int32 mr_platEx (int32 code = 4041, uint8* input, int32 input_len, uint8** output, int32* ` | 创建平台的电话本浏览对像。 |
| [mr_platEx(4042)](mr_platEx-4042.md) | `int32 mr_platEx (int32 code = 4042, uint8* input, int32 input_len, uint8** output, int32* ` | 获得选中的一个电话本记录的信息。 |
| [mr_platEx(4043)](mr_platEx-4043.md) | `int32 mr_platEx (int32 code = 4043, uint8* input, int32 input_len, uint8** output, int32* ` | 销毁电话本浏览对象。 |
| [mr_platEx(5)](mr_platEx-5.md) | `int32 mr_platEx (int32 code = 5, uint8* input, int32 input_len, uint8** output, int32* out` | MR_LIST_SET_FOCUS。 |
| [mr_platEx(5001)](mr_platEx-5001.md) | `int32 mr_platEx (int32 code = 5001, uint8* input, int32 input_len, uint8** output, int32* ` | 获取手机时间。 |
| [mr_platEx(5002)](mr_platEx-5002.md) | `int32 mr_platEx (int32 code = 5002, uint8* input, int32 input_len, uint8** output, int32* ` | 设置手机时间。 |
| [mr_platEx(5011)](mr_platEx-5011.md) | `int32 mr_platEx (int32 code = 5011, uint8* input, int32 input_len, uint8** output, int32* ` | 设置手机闹钟。（未实现） |
| [mr_platEx(5013)](mr_platEx-5013.md) | `int32 mr_platEx (int32 code = 5013, uint8* input, int32 input_len, uint8** output, int32* ` | 获得手机闹钟个数。（未实现） |
| [mr_platEx(5014)](mr_platEx-5014.md) | `int32 mr_platEx (int32 code = 5014, uint8* input, int32 input_len, uint8** output, int32* ` | 设置闹钟,到时间,启动获得天气的应用。 |
| [mr_platEx(5015)](mr_platEx-5015.md) | `int32 mr_platEx (int32 code = 5015, uint8* input, int32 input_len, uint8** output, int32* ` | 获得天气信息。 |
| [mr_platEx(5016)](mr_platEx-5016.md) | `int32 mr_platEx (int32 code = 5016, uint8* input, int32 input_len, uint8** output, int32* ` | 进入天气预报。 |
| [mr_platEx(5017)](mr_platEx-5017.md) | `int32 mr_platEx (int32 code = 5017, uint8* input, int32 input_len, uint8** output, int32* ` | 退出天气预报。 |
| [mr_platEx(5018)](mr_platEx-5018.md) | `int32 mr_platEx (int32 code = 5018, uint8* input, int32 input_len, uint8** output, int32* ` | 获取天气通知。 |
| [mr_platEx(5019)](mr_platEx-5019.md) | `int32 mr_platEx (int32 code = 5019, uint8* input, int32 input_len, uint8** output, int32* ` | 获取天气桌面信息。 |
| [mr_platEx(5101)](mr_platEx-5101.md) | `int32 mr_platEx (int32 code = 5101, uint8* input, int32 input_len, uint8** output, int32* ` | 修改菜单,TEXT,dialog等本地UI组件的左右软键文本。 |
| [mr_platEx(6000)](mr_platEx-6000.md) | `int32 mr_platEx (int32 code = 6000, uint8* input, int32 input_len, uint8** output, int32* ` | 查询是否支持气泡框接口。 |
| [mr_platEx(6001)](mr_platEx-6001.md) | `int32 mr_platEx (int32 code = 6001, uint8* input, int32 input_len, uint8** output, int32* ` | 显示气泡框。 |
| [mr_platEx(6002)](mr_platEx-6002.md) | `int32 mr_platEx (int32 code = 6002, uint8* input, int32 input_len, uint8** output, int32* ` | 隐藏气泡框。 |
| [mr_platEx(6003)](mr_platEx-6003.md) | `int32 mr_platEx (int32 code = 6003, uint8* input, int32 input_len, uint8** output, int32* ` | 是否在待机界面。 |
| [mr_platEx(6004)](mr_platEx-6004.md) | `int32 mr_platEx (int32 code = 6004, uint8* input, int32 input_len, uint8** output, int32* ` | 查询当前SIM卡的最后一次联网时间。 |
| [mr_platEx(6005)](mr_platEx-6005.md) | `int32 mr_platEx (int32 code = 6005, uint8* input, int32 input_len, uint8** output, int32* ` | 停止异步转后台。 |
| [mr_platEx](mr_platEx.md) | `int32 mr_platEx (int32 code, uint8* input, int32 input_len, uint8** output, int32* output_` | 扩展的平台调用接口，对应于应用层的mrc_platEx。 |
| [mr_playSound](mr_playSound.md) | `int32 mr_playSound(int type, const void* data, uint32 dataLen, int32 loop)` | 播放音频。 |
| [mr_printf](mr_printf.md) | `void mr_printf(const char *format, ...)` | 调试信息打印。 |
| [mr_read](mr_read.md) | `int32 mr_read(MR_FILE_HANDLE f, void *p, uint32 l)` | 读取文件内容到指定的缓冲区。 |
| [mr_recv](mr_recv.md) | `int32 mr_recv (int32 s, char *buf, int len)` | 接收数据。 |
| [mr_recvfrom](mr_recvfrom.md) | `int32 mr_recvfrom(int32 s, char *buf, int len, int32 *ip, uint16 *port)` | 接受数据报。 |
| [mr_registerAPP](mr_registerAPP.md) | `int32 mr_registerAPP(uint8 *p, int32 len, int32 index)` | 注册固化应用。 |
| [mr_remove](mr_remove.md) | `int32 mr_remove(const char* filename)` | 删除文件。 |
| [mr_rename](mr_rename.md) | `int32 mr_rename(const char* oldname, const char* newname)` | 文件重命名。 |
| [mr_resumeApp](mr_resumeApp.md) | `int32 mr_resumeApp(void)` | 恢复虚拟机运行。 |
| [mr_rmDir](mr_rmDir.md) | `int32 mr_rmDir(const char* name)` | 删除目录。 |
| [mr_save_mrp](mr_save_mrp.md) | `int32 mr_save_mrp(void *p, uint32 l)` | 文件下载判断与保存。 |
| [mr_seek](mr_seek.md) | `int32 mr_seek(MR_FILE_HANDLE f, int32 pos, int method)` | 设置文件读写指针。 |
| [mr_send](mr_send.md) | `int32 mr_send(int32 s, const char *buf, int len)` | 发送数据。 |
| [mr_sendSms](mr_sendSms.md) | `int32 mr_sendSms(char* pNumber, char*pContent, int32 flags)` | 发送一条短信。 |
| [mr_sendto](mr_sendto.md) | `int32 mr_sendto(int32 s, const char *buf, int len, int32 ip, uint16 port)` | 发送数据报。 |
| [mr_sleep](mr_sleep.md) | `int32 mr_sleep(uint32 ms)` | 让当前任务睡眠ms毫秒。方便调试的接口，可实现为空。 |
| [mr_smsIndiaction](mr_smsIndiaction.md) | `int32 mr_smsIndiaction(uint8 *pContent, int32 nLen, uint8 *pNum, int32 type)` | 新消息提示。 |
| [mr_socket](mr_socket.md) | `int32 mr_socket(int32 type, int32 protocol)` | 创建一个socket。 |
| [mr_start_dsm](mr_start_dsm.md) | `int32 mr_start_dsm(const char* entry)` | 通过入口参数来启动虚拟机。 |
| [mr_start_dsm_ex](mr_start_dsm_ex.md) | `int32 mr_start_dsm_ex(const char* path, const char* entry)` | 通过入口参数来启动虚拟机。 |
| [mr_start_dsmB](mr_start_dsmB.md) | `int32 mr_start_dsmB(const char* entry)` | 直接启动mrp文件，并且可以传参过去。 |
| [mr_start_dsmC](mr_start_dsmC.md) | `int32 mr_start_dsmC(const char* entry)` | 通过入口参数来启动虚拟机。 |
| [mr_startShake](mr_startShake.md) | `int32 mr_startShake(int32 ms)` | 启动震动。 |
| [mr_stop](mr_stop.md) | `int32 mr_stop(void)` | 停止虚拟机，并释放相关资源。 |
| [mr_stopSound](mr_stopSound.md) | `int32 mr_stopSound (int type)` | 停止播放音频。 |
| [mr_textCreate](mr_textCreate.md) | `int32 mr_textCreate(const char * title, const char * text, int32 type)` | 建立文本框。 |
| [mr_textRefresh](mr_textRefresh.md) | `int32 mr_textRefresh(int32 handle, const char * title, const char * text)` | 刷新文本框。 |
| [mr_textRelease](mr_textRelease.md) | `int32 mr_textRelease(int32 text)` | 释放文本框。 |
| [mr_timer](mr_timer.md) | `int32 mr_timer(void)` | 定时器通知函数。 |
| [mr_timerStart](mr_timerStart.md) | `int32 mr_timerStart(uint16 t)` | 定时器启动。 |
| [mr_timerStop](mr_timerStop.md) | `int32 mr_timerStop(void)` | 停止定时器。 |
| [mr_winCreate](mr_winCreate.md) | `int32 mr_winCreate(void)` | 创建可扩展窗体。 |
| [mr_winRelease](mr_winRelease.md) | `int32 mr_winRelease(int32 win)` | 释放窗体。 |
| [mr_write](mr_write.md) | `int32 mr_write(MR_FILE_HANDLE f, void *p, uint32 l)` | 写文件。 |
| [外部移植接口](外部移植接口.md) | `外部移植接口 SkyEngine外部移植接口是指虚拟机核心提供给外部使用的接口，移植层调用这些接口来使用SkyEngine提供的服务或将事件通知给SkyEngine。 Copyri` |  |
| [平台版本号规则](平台版本号规则.md) | `平台版本号规则 为了区分不同的手机平台，相同平台内的不同芯片及我们移植包版本，我们使用了一个32位的版本号来标识。这个版本号是由多个十进制的数段来表示，各个数段的表示如下表(1表示` |  |
| [扩展接口(mr_plat/mr_platEx)](扩展接口-mr_platmr_platEx.md) | `扩展接口 mr_plat和mr_platEx接口的主要目的是：在不对VM进行修改的前提下，可以扩展VM支持的功能，使得VM扩展功能不必在新增抽象接口。Mythroad透明调用这个接` |  |
| [接口跟踪表](接口跟踪表.md) | `移植层接口跟踪表 这里的版本号就是平台版本号规则里面的基线版本号，因为只有2-3两位表示支持的接口集，所以这里的第一和第三位都用x来表示。 版本号 新增支持接口集 发布时间及说明 ` |  |
| [数据账号接口](数据账号接口.md) | `MTK平台账号资料管理流程 Mythroad 联网流程介绍 (TCP) 初始化网络（mr_initNetwork）-&gt;创建连接（mr_socket） -&gt;连接服务器（m` |  |
| [电话本接口](电话本接口.md) | `电话本事件说明 1、 电话本的操作事件采用mr_event的形式通知上层应用。 2、 Mr_event的三个参数的具体说明如下： Mr_event(p1,p2,p3); p1 = ` |  |
