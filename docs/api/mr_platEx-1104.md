# mr_platEx(1104) - 删除一条短信

```c
int32 mr_platEx (int32 code = 1104, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

删除一条短信。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_DSM_DELETE_SMS_REQ |
| input_len | T_DSM_DELETE_SMS_REQ大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_WAITING : 请求成功
MR_FAILED : 请求失败
MR_IGNORE :
不支持该功能

## 备注

删除结果：
通过mr_event通知应用，各个参数的含义如下：
第一个：MR_SMS_OP_EVENT
第二个：MR_SMS_OP_DELETE
第三个：MR_SUCCESS
删除成功
MR_FAILED
删除失败
数据结果如下：
typedef struct
{
int32
index;//显示时候索引
int8 type; //MR_SMS_INBOX, MR_SMS_OUTBOX
}
T_DSM_DELETE_SMS_REQ;

## 相关

Copyright ?2005-20010 SKY-MOBI
