# mr_getDatetime

```c
int32 mr_getDatetime(mr_datetime* datetime)
```

## 说明

获取当前的日期。

## 参数

| 参数 | 说明 |
|---|---|
| datetime | 日期时间 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

获取系统日期时间。
mr_datetime格式如下：
typedef struct
{
uint16
year;
//年
uint8
month;
//月
uint8
day;
//日
uint8
hour;
//时，24小时制
uint8
minute;
//分
uint8
second;
//秒
}mr_datetime;

## 示例

```c
/*mrp code*/
mr_datetime dt;
mrc_getDatetime( &amp;dt );
mrc_printf( "Get
date time is %d:%d:%d,%d:%d:%d", dt.year, dt.month, dt.day, dt.hour,
dt.minute, dt.second );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
