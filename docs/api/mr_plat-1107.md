# mr_plat(1107) - 发送获得apn信息的请求

```c
int32 mr_plat(int32 code = 1107, int32 param)
```

## 说明

发送获得apn信息的请求。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_WAITING ：
发送成功
MR_FAILED ：
发送失败
MR_IGNORE ：
不支持该功能
注：处理结果通过mr_event返回给应用
mr_event的参数如下：
第一个：MR_DATA_ACCOUNT_EVENT（17）
第二个：MR_DATA_ACCOUNT_OP_GET（0）
第三个：MR_SUCCESS
获取成功，apn信息已经放置在缓存中，MR_FAILED
获取失败
当获取成功后调用mr_platEx(1108)获得缓冲中的内容

## 示例

```c
/*mrp code*/
mrc_plat( 1107, 0 );
mr_event事件处理：
case MR_DATA_ACCOUNT_EVENT:
{
switch ( wParam
)
{
case
MR_DATA_ACCOUNT_OP_GET:
CheckGetApnInfoResult(lParam);
break;
case
MR_DATA_ACCOUNT_OP_SET:
CheckSetApnInfoResult(lParam);
break;
default:
break;
}
break;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
