# mr_initNetwork

```c
int32 mr_initNetwork(MR_INIT_NETWORK_CB cb, const char *mode)
```

## 说明

网络初始化。

## 参数

| 参数 | 说明 |
|---|---|
| cb | 当网络初始化使用异步模式时，使用该回调函数通知引擎初始化结果 |
| mode | cmwap”的拨号方式。 |

拨号方式，”
cmnet”或”

## 返回值

MR_SUCCESS 同步模式，初始化成功，不再调用cb
MR_FAILED （立即感知的）失败，不再调用cb
MR_WAITING 使用回调函数通知引擎初始化结果.

## 备注

网络初始化，如果没有拨号，进行拨号操作。
这里需要注意的是，本文档描述的所有网络接口函数在实现时建议优先考虑采用非阻塞方式。
若网络初始化使用异步模式，使用回调函数通知引擎初始化结果。
typedef
int32 (*MR_INIT_NETWORK_CB)(int32 result);
回调函数参数说明：
result：
MR_SUCCESS初始化成功
MR_FAILED 初始化失败

## 示例

```c
/*mrp code*/
int32 cbInitNetwork(int32 result);
//回调函数
cbInitNetwork( mrc_initNetwork( cbInitNetwork, "cmnet" )
);
```

## 相关

Copyright ?2005-20010 SKY-MOBI
