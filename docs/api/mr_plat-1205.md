# mr_plat(1205) - 获取手机是否是触摸屏信息

```c
int32 mr_plat(int32 code = 1205, int32 param)
```

## 说明

获取手机是否是触摸屏信息。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_PLAT_VALUE_BASE + 0 ：非触摸屏
MR_PLAT_VALUE_BASE + 1
：触摸屏
MR_FAILED
：获取失败
MR_IGNORE
：不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
