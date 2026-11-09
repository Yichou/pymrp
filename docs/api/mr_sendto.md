# mr_sendto

```c
int32 mr_sendto(int32 s, const char *buf, int len, int32 ip, uint16 port)
```

## 说明

发送数据报。

## 参数

| 参数 | 说明 |
|---|---|
| s | socket句柄 |
| buf | 待发送数据buffer |
| len | 待发送数据字节数 |
| ip | 对端IP |
| port | 对端端口 |

## 返回值

&gt;=0表示实际发送的字节数，MR_FAILED表示出错.

## 示例

```c
/*mrp code*/
#define SOCKET_SENDBUFFER_SIZE 2048
const char
sSendBuffer[SOCKET_SENDBUFFER_SIZE ];
mrc_sendto( hSoc,
sSendBuffer, SOCKET_SENDBUFFER_SIZE, (int32*)&amp;ip,
(uint16*)&amp;port ); /*hSoc为mr_socket创建的句柄，ip为对端的IP地址，port为对端的端口号。*/
```

## 相关

Copyright ?2005-20010 SKY-MOBI
