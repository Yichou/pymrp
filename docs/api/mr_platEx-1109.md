# mr_platEx(1109) - 设置apn信息

```c
int32 mr_platEx (int32 code = 1109, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置apn信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_DSM_DATA_ACCOUNT数据结构 |
| input_len | T_DSM_DATA_ACCOUNT的大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_WAITING : 请求成功
MR_FAILED : 请求失败
MR_IGNORE :
不支持该功能

## 备注

设置结果异步通过mr_event返回，
mr_event各个参数的值如下：
第一个参数：MR_DATA_ACCOUNT_EVENT（17）
第二个参数：MR_DATA_ACCOUNT_OP_SET（1）
第三个参数：MR_FAILED:设置失败
MR_SUCCESS:设置成功

## 相关

Copyright ?2005-20010 SKY-MOBI
