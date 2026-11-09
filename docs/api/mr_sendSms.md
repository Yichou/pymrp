# mr_sendSms

```c
int32 mr_sendSms(char* pNumber, char*pContent, int32 flags)
```

## 说明

发送一条短信。

## 参数

| 参数 | 说明 |
|---|---|
| pNumber | 电话号码，ASCII码 |
| pContent | 消息内容，ASCII码或Unicode码，由flags参数决定 |
| flags | bit：保留 |

0～2bit：编码类型
MR_ENCODE_ASCII:
ASCII码
MR_ENCODE_UNICODE:
Unicode码,
网络字节序。
3bit：是否隐藏状态报告
1：隐藏状态报告
0：不隐藏状态报告
4bit：是否隐藏发送结果（成功/失败）提示
1：隐藏
0：不隐藏5～31

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED,
未准备好返回MR_IGNORE.

## 示例

```c
/*mrp code*/
#define SEND_SMS_TO "10086"
#define SEND_CONTENT
"Hello: Sky Test!"
mrc_sendSms( SEND_SMS_TO, SEND_CONTENT, 0
);
```

## 相关

Copyright ?2005-20010 SKY-MOBI
