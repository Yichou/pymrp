# mr_plat(1004) - 设置使用SIM卡

```c
int32 mr_plat(int32 code = 1004, int32 param)
```

## 说明

多sim卡待机时设置所用sim卡。

## 参数

| 参数 | 说明 |
|---|---|
| param | 中simId，由手机或移植处定义） |

Sim卡id（对应platEx（1307）结构MR_DUALSIM_SET_T

## 返回值

MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。

## 相关

Copyright ?2005-20010 SKY-MOBI
