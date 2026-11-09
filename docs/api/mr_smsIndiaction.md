# mr_smsIndiaction

```c
int32 mr_smsIndiaction(uint8 *pContent, int32 nLen, uint8 *pNum, int32 type)
```

## 说明

新消息提示。

## 参数

| 参数 | 说明 |
|---|---|
| pContent | 接收到的短信内容 |
| nLen | 短信内容长度 |
| pNum | 短信发送者号码 |
| type | 网络字节序 |

MR_ENCODE_ASCII: ASCII码
MR_ENCODE_UNICODE: Unicode码,

## 返回值

操作成功返回MR_SUCCESS,操作失败返回MR_FAILED,不处理返回MR_IGNORE.
在返回非MR_IGNORE的情况下需要删除该短信。

## 备注

当手机收到短消息时调用该函数。该函数检测新来的消息是否为SkyEngine配置消息，如果是SkyEngine配置消息，则进行对应的配置操作，返回MR_SUCCESS或MR_FAILED；不是SkyEngine配置消息则返回MR_IGNORE。每当手机收到新来的短消息，调用这个接口，如果返回值是MR_SUCCESS或MR_FAILED，则需要丢弃(删除)该消息。如果返回值是MR_IGNORE，该消息不是SkyEngine配置消息，无须进行特殊处理。

## 相关

Copyright ?2005-20010 SKY-MOBI
