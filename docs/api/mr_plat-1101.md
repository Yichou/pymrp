# mr_plat(1101) - 获得短信信箱中短息的条数

```c
int32 mr_plat(int32 code = 1101, int32 param)
```

## 说明

获得短信信箱中短息的条数。

## 参数

| 参数 | 说明 |
|---|---|
| param | }MR_MSG_STATUS; |

MR_SMS_INBOX：收件箱
MR_SMS_OUTBOX：发件箱
MR_SMS_DRAFTS：草稿箱注各个枚举值：
typedef
enum
{
MR_SMS_NOBOX ,
MR_SMS_UNREAD,
MR_SMS_INBOX,
MR_SMS_OUTBOX,
MR_SMS_DRAFTS,
MR_SMS_AWAITS,
MR_SMS_DATA,
MR_SMS_UNSENT,
MR_SMS_READED,
MR_SMS_SENT

## 返回值

MR_FAILED：操作失败
短信条数加上MR_PLAT_VALUE_BASE。

## 相关

Copyright ?2005-20010 SKY-MOBI
