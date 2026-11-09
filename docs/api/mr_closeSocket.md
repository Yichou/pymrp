# mr_closeSocket

```c
int32 mr_closeSocket(int32 s)
```

## 说明

关闭socket。

## 参数

| 参数 | 说明 |
|---|---|
| s | socket 句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
int32 hSoc = 0;
hSoc = mrc_socket( MR_SOCK_STREAM, MR_IPPROTO_TCP
);
mrc_closeSocket( hSoc );
```

## 相关

mr_socket
Copyright ?2005-20010 SKY-MOBI
