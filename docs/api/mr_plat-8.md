# mr_plat(8) - 设置wap下载的.nes保存所使用的存储器

```c
int32 mr_plat(int32 code = 8, int32 param)
```

## 说明

设置wap下载的.nes保存所使用的存储器。

## 参数

| 参数 | 说明 |
|---|---|
| param | 第二外插存储设备 |

各种盘符标志的定义与platex（1204）必须相同，不同的是以ascii码值表示（不区分大小写），如：
‘B’
或‘b’： 普通用户可操作存储盘（即可usb连接在PC上操作）
‘C’：
外插存储设备，如mmc，sd，t-flash等
‘D’：

## 返回值

MR_SUCCESS ：成功
MR_FAILED ：失败
MR_IGNORE
：不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
