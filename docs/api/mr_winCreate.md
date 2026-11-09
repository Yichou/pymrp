# mr_winCreate

```c
int32 mr_winCreate(void)
```

## 说明

创建可扩展窗体。

## 参数

| 参数 | 说明 |
|---|---|
|  |  |

## 返回值

&gt;0 为窗体句柄，MR_FAILED表示失败.

## 备注

创建一个可扩展窗体，并返回可扩展窗体句柄。可扩展窗体是一种可动态下载更新的窗体模式，可动态扩充功能，可以实现进度条、扩展控件、交互小应用等等强大的扩充功能。
可扩展窗体创建之后，需要将用户的按键和触摸屏事件构造成SkyEngine消息，通过mr_event函数传送给SkyEngine，按键事件的消息类型为MR_KEY_PRESS、MR_KEY_RELEASE，触摸屏事件的消息类型为MR_MOUSE_DOWN、MR_MOUSE_UP。

## 示例

```c
/*mrp code*/
int32 hExtWnd = 0;
hExtWnd = mrc_winCreate();
```

## 相关

mr_winRelease
Copyright ?2005-20010 SKY-MOBI
