# mr_getUserInfo

```c
int32 mr_getUserInfo(mr_userinfo* info)
```

## 说明

获取手机相关信息。

## 参数

| 参数 | 说明 |
|---|---|
| info | 手机信息 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

返回手机相关信息。mr_userinfo说明如下：
typedef
struct
{
uint8
IMEI[16]; //IMEI len eq
15
uint8
IMSI[16]; //IMSI len not more then
15
char
manufactory[8];
//厂商名，最大7个字符，空字节填\0
char
type[8]; //mobile
type，最大7个字符，空字节填\0
uint32
ver;
//移植版本, 参考移植版本号规则
uint8
spare[12];
//备用
}mr_userinfo;

## 示例

```c
/*mrp code*/
mr_userinfo info;
mrc_getSysInfo( &amp;info );
mrc_printf(
"manufactory:%s,type:%s,version:%d,IMEI:%s,IMSI:%s", info.manufactory,
info.type, info.ver, info.IMEI, info.IMSI );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
