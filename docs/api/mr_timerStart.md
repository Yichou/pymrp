# mr_timerStart

```c
int32 mr_timerStart(uint16 t)
```

## 说明

定时器启动。

## 参数

| 参数 | 说明 |
|---|---|
| t | 时间间隔，单位为毫秒 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

此定时器函数为单次函数，VM调用此函数来启动一次定时操作，但timeout后，需要调用外部移植接口mr_timer来通知VM。

## 相关

mr_timer
mr_timerStop
Copyright ?2005-20010 SKY-MOBI
