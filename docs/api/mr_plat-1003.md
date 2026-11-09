# mr_plat(1003) - 激活后台程序到前台

```c
int32 mr_plat(int32 code = 1003, int32 param)
```

## 说明

将后台程序切换到前台运行。

## 参数

| 参数 | 说明 |
|---|---|
| param | 要激活到前台的应用的appid |

## 返回值

MR_SUCCESS ： 激活成功
MR_FAILED ：激活失败
MR_IGNORE
：不支持该功能

## 备注

通知移植层将后台运行的应用激活到前台来运行。当激活后，移植层将通过mr_event()这个函数来通知应用。
注：mr_event 通知应用的参数说明：
mr_event(MR_LOCALUI_EVENT, MR_LOCALUI_APPRESUME,
0);
MR_LOCALUI_APPRESUME 2
MR_LOCALUI_EVENT 10

## 示例

```c
/*mrp code*/
int32 AwakeApp(int32
appid)
{
int32 ret =
MR_FAILED;
ret =
mrc_plat(1003,appid);
if (ret ==
MR_SUCCESS)
{
/*唤醒成功需要停止后台icon的闪动，这里建议在mr_event(MR_LOCALUI_EVENT, MR_LOCALUI_APPRESUME,
0);
函数中进行调用本接口，这样可以做到主动唤醒和被动唤醒都可以关闭后台icon的闪动；*/
mrc_plat(1006,appid);
}
return
ret;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
