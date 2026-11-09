# mr_platEx(5015) - 获得天气信息

```c
int32 mr_platEx (int32 code = 5015, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得天气信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | t_mr_weather_info |
| input_len | 输入参数大小（字节数） |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构定义
.天气情况:
typedef enum
{
E_SUNNY,
//晴
E_RAIN,//雨天
E_SNOW,//雪
E_CLOUDY,//多云
}e_weather_info;
时间结构
typedef struct
{
int hour;
int
min;
}t_sun_time;
日期结构
typedef struct
{
int year;
int
month;
int day;
}t_dsm_date;
天气信息
typedef struct
{
int weather;// 天气
int high;//最高温度
int
low;//最低温度
int wind;//风力
int barometerj;//大气压强
int
humidity;//湿度
int visibility ;//可见度
int dewpoint;//露点
t_sun_time
sunrise;//日出时间
t_sun_time sunset;//日落时间
char
city[64];//所在城市
t_dsm_date
date;//天气的日期,表示哪天的天气.
}t_mr_weather_info;

## 相关

Copyright ?2005-20010 SKY-MOBI
