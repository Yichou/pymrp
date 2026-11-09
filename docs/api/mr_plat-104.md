# mr_plat(104) - 销毁窗口而不画屏幕

```c
int32 mr_plat(int32 code = 104, int32 param)
```

## 说明

销毁窗口而不画屏幕。（BASE WIN以上的窗口都销毁）。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_IGNORE ：不支持该功能
MR_SUCCESS：销毁成功

## 备注

这个接口会负责把base win以上的创建对象和申请的资源都释放掉，
要在启动另外一个应用之前调用这个接口，调用了这个接口之后只需
要销毁VM中的窗口，请不要再调用d_release
之类的释放本地接口
函数。

## 相关

Copyright ?2005-20010 SKY-MOBI
