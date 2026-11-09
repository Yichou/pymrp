# mr_plat(1106) - 获得短信中心

```c
int32 mr_plat(int32 code = 1106, int32 param)
```

## 说明

发送获得短信中心的号码的请求。

## 参数

| 参数 | 说明 |
|---|---|
| param | 应用编号 |

## 返回值

MR_WAITING ： 发送请求成功
MR_FAILED ：设置失败
MR_IGNORE
：不支持该功能
注：处理结果通过mr_event返回给应用
mr_event的参数如下：
第一个：MR_SMS_GET_SC（16）
第二个：ascii编码的短信中心的字符串的地址，地址为0标志获得失败
第三个：0

## 相关

Copyright ?2005-20010 SKY-MOBI
