# mr_recv

```c
int32 mr_recv (int32 s, char *buf, int len)
```

## 说明

接收数据。

## 参数

| 参数 | 说明 |
|---|---|
| s | socket 句柄 |
| buf | 接收数据缓冲区 |
| len | 缓冲区大小 |

## 返回值

&gt;=0表示实际接收的数据大小，MR_FAILED表示出错.

## 示例

```c
/*mrp code*/
#define SOCKET_RECVBUFFER_SIZE 2048
static UCHAR
sRecvBuffer[SOCKET_RECVBUFFER_SIZE]; //接收数据缓冲区
mrc_recv( hSoc,
(PSTR)sRecvBuffer, SOCKET_RECVBUFFER_SIZE );
//hSoc为mr_socket创建的socket句柄
```

## 相关

Copyright ?2005-20010 SKY-MOBI
