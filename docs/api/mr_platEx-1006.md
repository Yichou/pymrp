# mr_platEx(1006) - 启动平台QQ

```c
int32 mr_platEx (int32 code = 1006, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

启动平台QQ。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_custStartParam_st结构的指针 |
| input_len | mr_custStartParam_st结构的长度 |
| output | 输出参数的起始地址 |
| output_len | 输出参数大小（字节数） |
| cb | 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下：
typedef
void (*MR_PLAT_EX_CB)(uint8* output, int32
output_len);
若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。
输入参数如下：
typedef
struct
{
int32 appid; //sky应用唯一标志
uint8 describe[20]; //应用标志符 – 可填入list的启动参数as："mtkqq"
uint8* param; //启动验证参数
int32
paramLen; //启动验证参数长度
}mr_custStartParam_st;
input：
mr_custStartParam_st 结构的指针
input_len：mr_custStartParam_st
结构的长度

## 示例

```c
int32
StartPlatAPP(void)
{
mr_userinfo info={0};
mr_datetime
datetime={0};
int32 ret
= MR_FAILED;
mrc_getDatetime(&amp;datetime);
mrc_getSysInfo(&amp;info);
{
static mr_custStartParam_st
st={0};
static uint8 encode[128] =
{0};
uint8
buf[64]={0};
sprintf((char*)buf,"%s&amp;%s&amp;%s&amp;%d",info.manufactory,info.type,info.IMEI,datetime.month);
ret = mrc_encode(buf, strlen((char*)buf),
encode);
if (ret &gt;
0)
{
MR_PLAT_EX_CB cb = NULL;
mrc_setReloadFile(NULL,
NULL);
st.appid
=
203104;
strcpy((char*)st.describe,(char*)"qq2009r");
st.param = encode;//验证信息为加密后的厂商、机型信息、IMEI号和当前的月份；
st.paramLen =
strlen((char*)encode);
ret = mrc_platEx(1006, (uint8 *)&amp;st, sizeof(mr_custStartParam_st), NULL,
NULL,&amp;cb);
}
else
ret
= MR_FAILED;
}
return ret；
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
