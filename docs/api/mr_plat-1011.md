# mr_plat(1011) - 设置收到新短信的时候是否显示提示界面

```c
int32 mr_plat(int32 code = 1011, int32 param)
```

## 说明

设置收到新短信的时候是否显示提示界面。

## 参数

| 参数 | 说明 |
|---|---|
| param | 0：不显示新短信提示 |

1：显示新短信提示

## 返回值

MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。

## 相关

Copyright ?2005-20010 SKY-MOBI
