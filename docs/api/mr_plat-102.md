# mr_plat(102) - 告知驱动PCM写入数据的绝对地址

```c
int32 mr_plat(int32 code = 102, int32 param)
```

## 说明

告知驱动PCM写入数据的绝对地址。（再根据数据的其实地址可以算出等待播放的数据量）

## 参数

| 参数 | 说明 |
|---|---|
| param | PCM写入数据的绝对地址 |

## 返回值

MR_SUCCESS 成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
