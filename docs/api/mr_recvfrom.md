# mr_recvfrom

```c
int32 mr_recvfrom(int32 s, char *buf, int len, int32 *ip, uint16 *port)
```

## 说明

接受数据报。

## 参数

| 参数 | 说明 |
|---|---|
| s | socket 句柄 |
| buf | 接收数据buffer |
| len | buffer长度 |
| ip | 对端的IP地址 |
| port | 对端的端口号 |

## 返回值

&gt;=0表示实际接收到的数据字节数，MR_FAILED表示出错.

## 示例

```c
/*mrp code*/
#define SOCKET_RECVBUFFER_SIZE 2048
static UCHAR
sRecvBuffer[SOCKET_RECVBUFFER_SIZE]; //接收数据缓冲区
mrc_recvfrom(
hSoc, (PSTR)sRecvBuffer, SOCKET_RECVBUFFER_SIZE, (int32*)&amp;ip,
(uint16*)&amp;port );
/*hSoc为mr_socket创建的句柄，ip为对端的IP地址，port为对端的端口号。*/
```

## 相关

Copyright ?2005-20010 SKY-MOBI
