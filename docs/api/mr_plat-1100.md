# mr_plat(1100) - 获得短信操作的状态

```c
int32 mr_plat(int32 code = 1100, int32 param)
```

## 说明

获得短信操作的状态。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_SMS_NOT_READY = MR_PLAT_VALUE_BASE：短信模块初始化中
MR_SMS_READY=
MR_PLAT_VALUE_BASE+1 ：短信模块初始化完毕可以操作。

## 相关

Copyright ?2005-20010 SKY-MOBI
