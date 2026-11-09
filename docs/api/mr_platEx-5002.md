# mr_platEx(5002) - 设置手机时间

```c
int32 mr_platEx (int32 code = 5002, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置手机时间。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向MYTIME数据结构 |
| input_len | MYTIME 的大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构如下，
typedef struct MYTIME
{
kal_uint16
nYear;
kal_uint8 nMonth;
kal_uint8
nDay;
kal_uint8 nHour;
kal_uint8
nMin;
kal_uint8 nSec;
kal_uint8
DayIndex;
} MYTIME;

## 相关

Copyright ?2005-20010 SKY-MOBI
