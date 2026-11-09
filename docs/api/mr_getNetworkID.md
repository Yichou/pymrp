# mr_getNetworkID

```c
int32 mr_getNetworkID(void)
```

## 说明

获取网络ID。

## 参数

| 参数 | 说明 |
|---|---|
|  |  |

## 返回值

返回取值如下：
enum {
MR_NET_ID_MOBILE,
//移动GSM
MR_NET_ID_CN, //
联通GSM
MR_NET_ID_CDMA,
//联通CDMA
MR_NET_ID_NONE
//未插卡或网络错误
};

## 示例

```c
/*mrp code*/
int32 netID;
netID = mrc_getNetworkID();
```

## 相关

Copyright ?2005-20010 SKY-MOBI
