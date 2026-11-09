# mr_platEx(1108) - 从缓存中读取apn信息

```c
int32 mr_platEx (int32 code = 1108, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

从缓存中读取apn信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS : 请求成功
MR_FAILED : 请求失败
MR_IGNORE :
不支持该功能

## 备注

Apn的数据结果如下：
typedef struct
{
uint8
authentication_type;
uint8
user_name[32];
uint8 password[32];
uint8 dns[4];
uint8
apn[100];
}T_DSM_DATA_ACCOUNT;

## 相关

Copyright ?2005-20010 SKY-MOBI
