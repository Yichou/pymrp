# mr_socket

```c
int32 mr_socket(int32 type, int32 protocol)
```

## 说明

创建一个socket。

## 参数

| 参数 | 说明 |
|---|---|
| type | MR_SOCK_DGRAM |
| protocol | MR_IPPROTO_UDP |

Socket类型：
MR_SOCK_STREAM
具体协议类型:
MR_IPPROTO_TCP，

## 返回值

&gt;=0 socket句柄，MR_FAILED表示失败.

## 示例

```c
/*mrp code*/
int32 hSoc = 0;
hSoc = mrc_socket( MR_SOCK_STREAM, MR_IPPROTO_TCP
);
```

## 相关

mr_closeSocket
Copyright ?2005-20010 SKY-MOBI
