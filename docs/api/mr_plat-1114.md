# mr_plat(1114) - 获得当前激活的主题的appid

```c
int32 mr_plat(int32 code = 1114, int32 param)
```

## 说明

获得当前激活的主题的app id。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

&gt;1000 ： 当前激活的主题的app id是返回值-1000
1000：当前没有设置主题
MR_FAILED
：设置失败
MR_IGNORE ：不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
