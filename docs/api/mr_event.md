# mr_event

```c
int32 mr_event(int16 type, int32 param1, int32 param2)
```

## 说明

发送事件给虚拟机，在应用层将通过mrc_event接收到相应的消息。

## 参数

| 参数 | 说明 |
|---|---|
| type | 虚拟机预定义的事件类型，各个事件类型的具体定义请参考MR_EVENT_E |
| param1 | 参数1，由事件定义 |
| param2 | 参数2，由事件定义 |

## 返回值

当成功将事件发送到虚拟机并进行处理后将返回MR_SUCCESS,
如果未将事件传到虚拟机将返回MR_FAILED，如果是虚拟机不支持的事件将返回MR_IGNORE。在返回值上这里有一点要特别注意，mr_event的返回值不等于mrc_event的返回值，某些时候我们可能期望通过mr_event来调用应用中的相应功能，但切记，通过mrc_event返回的值，在平台的移植层是得不到的。

## 备注

在移植层将本地的事件转换成虚拟机事件后，需要通过mr_event
将事件发送到虚拟机，应用层会由mrc_event接收，这里的发送是同步的，其实就是同步的调用过程，mr_event发送的事件遵循公共且唯一的定义，各个事件可带有1至2个参数，参数的个数和具体的移植由事件本身定义，应用和移植层遵循此协议。
事件定义
enum {
MR_KEY_PRESS, /*按键按下事件, param1
为按键值*/
MR_KEY_RELEASE, /*1*/
MR_MOUSE_DOWN, /*2*/
MR_MOUSE_UP, /*3*/
MR_MENU_SELECT, /*4*/
MR_MENU_RETURN, /*5*/
MR_DIALOG_EVENT, /*6*/
MR_SMS_INDICATION, /*7*/
MR_EVENT_EXIT, /*8*/
MR_SMS_RESULT, /*9*/
MR_LOCALUI_EVENT, /*10*/
MR_OSD_EVENT, /*11*/
MR_MOUSE_MOVE, /*12*/
MR_ERROR_EVENT, /*13执行异常通过这个事件来通知*/
MR_PHB_EVENT,
MR_SMS_OP_EVENT,
MR_SMS_GET_SC,
MR_DATA_ACCOUNT_EVENT,
MR_MOTION_EVENT,
MR_MCHAT_EVENT =
100,
}MR_EVENT_E;

## 相关

Copyright ?2005-20010 SKY-MOBI
