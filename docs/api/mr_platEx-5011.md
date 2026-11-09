# mr_platEx(5011) - 设置手机闹钟

```c
int32 mr_platEx (int32 code = 5011, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置手机闹钟。（未实现）

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向mr_alarm_set_req_struct结构的指针 |
| input_len | mr_alarm_set_req_struct大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构：
typedef struct
{
UINT8
alarm_index;/*第几个闹铃*/
UINT8 recurr;/*一个星期哪一天闹铃*/
DSMTIME
dsm_time;
}mr_alarm_set_req_struct;
说明:闹钟设置只针对 小时,分.

## 相关

Copyright ?2005-20010 SKY-MOBI
