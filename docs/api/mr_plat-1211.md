# mr_plat(1211) - 生成随机数

```c
int32 mr_plat(int32 code = 1221, int32 param)
```

## 说明

调用平台接口产生随即数。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

要产生的随即数的范围(正整数)
返回：MR_PLAT_VALUE_BASE + 随机数
：产生随即数成功
MR_FAILED
：产生随机数失败
MR_IGNORE
：不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
