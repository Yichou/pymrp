# mr_send

```c
int32 mr_send(int32 s, const char *buf, int len)
```

## 说明

发送数据。

## 参数

| 参数 | 说明 |
|---|---|
| s | socket 句柄 |
| buf | 待发送数据buffer |
| len | 待发送数据长度 |

## 返回值

&gt;= 0表示实际发送数据的字节数，MR_FAILED表示出错.

## 示例

```c
/*mrp code*/
#define SOCKET_SENDBUFFER_SIZE 2048
const char
sSendBuffer[SOCKET_SENDBUFFER_SIZE ];
mrc_send( hSoc,
sSendBuffer, SOCKET_SENDBUFFER_SIZE );
//hSoc为mr_socket创建的句柄
```

## 相关

Copyright ?2005-20010 SKY-MOBI
