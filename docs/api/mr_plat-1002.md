# mr_plat(1002) - 设置socket的连接等待时间

```c
int32 mr_plat(int32 code = 1002, int32 param)
```

## 说明

设置socketconnect等待时间“废止“。

## 参数

| 参数 | 说明 |
|---|---|
| param | 超时时间，单位ms |

## 返回值

MR_SUCCESS ： 设置成功
MR_FAILED ：设置失败
MR_IGNORE
：不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
