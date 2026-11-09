# mr_registerAPP

```c
int32 mr_registerAPP(uint8 *p, int32 len, int32 index)
```

## 说明

注册固化应用。

## 参数

| 参数 | 说明 |
|---|---|
| entry | 固化应用的数据块内存指针 |
| len | 固化应用的数据块长度 |
| index | 1922版本起扩展到0-19） |

注册位置,取值0-9（VM

## 返回值

成功返回MR_SUCCESS, 失败返回MR_FIALED.

## 相关

Copyright ?2005-20010 SKY-MOBI
