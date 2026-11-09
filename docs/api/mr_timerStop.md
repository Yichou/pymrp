# mr_timerStop

```c
int32 mr_timerStop(void)
```

## 说明

停止定时器。

## 参数

| 参数 | 说明 |
|---|---|
|  |  |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

用于停止mr_timerStart启动的定时器，如果之前没有调用过mr_timerStart,多调用此函数应该不会产生其他影响。

## 相关

mr_timer
mr_timerStart
Copyright ?2005-20010 SKY-MOBI
