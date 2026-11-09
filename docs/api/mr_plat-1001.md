# mr_plat(1001) - 查询socket的连接状态

```c
int32 mr_plat(int32 code = 1001, int32 param)
```

## 说明

异步connect状态查询。

## 参数

| 参数 | 说明 |
|---|---|
| param | Socket句柄 |

## 返回值

MR_SUCCESS ： 连接成功
MR_FAILED ：连接失败
MR_WAITING
：连接中
MR_IGNORE ：不支持该功能

## 备注

轮询 socket connect 状态（主要用于TCP的异步连接。）

## 相关

Copyright ?2005-20010 SKY-MOBI
