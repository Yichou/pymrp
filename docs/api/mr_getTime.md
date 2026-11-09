# mr_getTime

```c
uint32 mr_getTime(void)
```

## 说明

获取毫秒时间。

## 参数

| 参数 | 说明 |
|---|---|
|  |  |

## 返回值

当前的毫秒时间.

## 备注

获取系统时间，单位毫秒。系统时间可以以SkyEngine引擎启动之前的任意时刻为起始时间，返回从起始时间到目前经过的毫秒数。例如这个函数可以实现为返回系统启动后经过的毫秒数。

## 示例

```c
/*mrp code*/
int32 tm = 0;
tm = mrc_getUptime();
mrc_printf( "time_ms = %d", tm
);
```

## 相关

Copyright ?2005-20010 SKY-MOBI
