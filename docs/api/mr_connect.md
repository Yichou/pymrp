# mr_connect

```c
int32 mr_connect(int32 s, int32 ip, uint16 port, int32 type)
```

## 说明

建立 socket 连接。

## 参数

| 参数 | 说明 |
|---|---|
| s | socket 句柄 |
| ip | 对端ip地址 |
| port | 对端端口号 |
| type | //非阻塞方式（异步方式） |

MR_SOCKET_BLOCK
//阻塞方式（同步方式）
MR_SOCKET_NONBLOCK

## 返回值

MR_SUCCESS 成功
MR_FAILED 失败
MR_WAITING 使用异步方式进行连接，VM需要轮询该socket的状态以获知连接状况

## 备注

初始化SkyEngine引擎，并运行指定的应用。当SkyEngine引擎启动时会调用mr_mem_get获取引擎需要的内存。
mr_mem_get函数由移植者实现，以取得引擎需要的内存。entry是SkyEngine入口参数。

## 示例

```c
/*mrp code*/
#define IPADDR(a,b,c,d) (((uint32)a)&lt;&lt;24
((uint32)b)&lt;&lt;16 | ((uint32)c)&lt;&lt;8 | ((uint32)d))
int32 hSoc =
0;
hSoc = mrc_socket( MR_SOCK_STREAM, MR_IPPROTO_TCP );
mrc_connect(
hSoc , IPADDR(119, 75, 218, 45), 80, MR_SOCKET_NONBLOCK);
```

## 相关

mr_socket
mr_closeSocket
Copyright ?2005-20010 SKY-MOBI
