# mr_plat(4) - nes特殊操作

```c
int32 mr_plat(int32 code = 4, int32 param)
```

## 说明

nes特殊操作。

## 参数

| 参数 | 说明 |
|---|---|
| param | 1：恢复 |

0：禁闭

## 返回值

MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。

## 备注

关闭、恢复平台某些可能与nes模拟器冲突的资源。如：信息提示音、低压警告音等与nes的pcm播放冲突（iram资源。

## 相关

Copyright ?2005-20010 SKY-MOBI
