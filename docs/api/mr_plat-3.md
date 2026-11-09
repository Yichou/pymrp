# mr_plat(3) - 获取虚拟键状态

```c
int32 mr_plat(int32 code = 3, int32 param)
```

## 说明

获取虚拟键对应的按下、弹起状态。

## 参数

| 参数 | 说明 |
|---|---|
| param | 虚拟键的index |

## 返回值

MR_PLAT_VALUE_BASE + 0 ： 弹起（un-pressed）
MR_PLAT_VALUE_BASE +
1 ：
按下（pressed）
MR_IGNORE
： 不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
