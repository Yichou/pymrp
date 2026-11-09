# mr_getHostByName

```c
int32 mr_getHostByName(const char *name, MR_GET_HOST_CB cb)
```

## 说明

域名解析。

## 参数

| 参数 | 说明 |
|---|---|
| name | 主机名 |
| cb | 回调函数 |

## 返回值

MR_FAILED （立即感知的）失败，不再调用cb
MR_WAITING 使用回调函数通知引擎获取IP的结果
其他值 同步模式，立即返回的IP地址，不再调用cb

## 备注

通过主机名获得该主机的IP地址值，如果一个主机的IP地址为218.18.95.203，则值为218&lt;&lt;24 + 18&lt;&lt;16
+ 95&lt;&lt;8 + 203 =
0xda125fcb。
若获取主机IP使用异步模式，使用回调函数通知引擎获取IP的结果。
typedef int32
(*MR_GET_HOST_CB)(int32 ip);
回调函数参数说明：
ip： MR_FAILED
获取IP失败
其他值 IP地址

## 示例

```c
/*mrp code*/
int32 cbGetHost(int32 ip); //回调函数
cbGetHost(
mrc_getHostByName( "www.baidu.com",
cbGetHost ) );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
