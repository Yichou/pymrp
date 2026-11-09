# mr_plat(1206) - 获取手机当前设置的语言

```c
int32 mr_plat(int32 code = 1206, int32 param)
```

## 说明

获取手机当前设置的语言。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_PLAT_VALUE_BASE + 0 ：中文
MR_PLAT_VALUE_BASE + 1
：英文
MR_FAILED
：获取失败
MR_IGNORE
：不支持该功能
注：其他语言的键值可以放在“英文”之后返

## 相关

Copyright ?2005-20010 SKY-MOBI
