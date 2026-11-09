# mr_platEx(4033) - 获取电话本操作状态

```c
int32 mr_platEx (int32 code = 4033, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得电话本操作的状态。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_PHB_NOT_READY （1004）初始化中
MR_PHB_READY
（1002）可以进行操作

## 相关

Copyright ?2005-20010 SKY-MOBI
