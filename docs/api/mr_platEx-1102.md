# mr_platEx(1102) - 获得指定一条短信的信息

```c
int32 mr_platEx (int32 code = 1102, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得指定一条短信的信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_DSM_GET_SMS_INFO_REQ |
| input_len | T_DSM_GET_SMS_INFO_REQ大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_WAITING : 请求成功
MR_FAILED : 请求失败
MR_IGNORE :
不支持该功能

## 备注

短信的数据结构是：T_DSM_MSG_INFO
数据结果如下：
typedef struct
{
int32
index;//显示时候索引
int8 type; //MR_SMS_INBOX,
MR_SMS_OUTBOX
}T_DSM_GET_SMS_INFO_REQ;
typedef struct
{
int8 t_stamp [6];
/*t_stamp[0]年t_stamp[1]月t_stamp[2]日
t_stamp[3]时t_stamp[4]分t_stamp[5]秒*/
int8
num[21]; /*发送方号码*/
int8 sms_status; /*Read or Unread
*/
int8 sms_storage; /* MR_SMS_STORAGE_ME ,
MR_SMS_STORAGE_SIM*/
}T_DSM_MSG_INFO;

## 相关

Copyright ?2005-20010 SKY-MOBI
