# mr_stop

```c
int32 mr_stop(void)
```

## 说明

停止虚拟机，并释放相关资源。

## 参数

| 参数 | 说明 |
|---|---|
|  |  |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

退出SkyEngine并释放相关资源。引擎退出时会调用mr_mem_free函数释放由mr_mem_get函数取得的内存。

## 相关

Copyright ?2005-20010 SKY-MOBI
