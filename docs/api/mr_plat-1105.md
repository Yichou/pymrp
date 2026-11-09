# mr_plat(1105) - 发送获得手机和sim卡存储空间

```c
int32 mr_plat(int32 code = 1105, int32 param)
```

## 说明

发送获得手机和sim卡存储空间的容量的请求。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_WAITING ： 发送请求成功
MR_FAILED ：调用失败
注：处理结果通过mr_event返回给应用
mr_event的参数如下：
第一个：MR_SMS_OP_EVENT（15）
第二个：MR_SMS_OP_GET_ME_SIZE
：表示第三个参数是手机上容量
MR_SMS_OP_GET_SIM_SIZE：表示第三个参数是sim卡上容量
第三个：短信的容量
enum
{
MR_SMS_OP_GET_ME_SIZE,
MR_SMS_OP_GET_SIM_SIZE,
MR_SMS_OP_DELETE,
MR_SMS_OP_GET_MSG_CONTENT
};

## 相关

Copyright ?2005-20010 SKY-MOBI
