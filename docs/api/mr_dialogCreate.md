# mr_dialogCreate

```c
int32 mr_dialogCreate(const char * title, const char * text, int32 type)
```

## 说明

创建对话框。

## 参数

| 参数 | 说明 |
|---|---|
| title | 对话框的标题，unicode编码，网络字节序。 |
| text | 对话框内容，unicode编码，网络字节序。 |
| type | “取消”键。 |

对话框类型：
MR_DIALOG_OK：对话框有“确定”键。
MR_DIALOG_OK_CANCEL：对话框有“确定”和“取消”键。
MR_DIALOG_CANCEL：对话框有

## 返回值

&gt;0 为对话框句柄，MR_FAILD表示失败.

## 备注

创建一个对话框，并返回对话框句柄。当对话框显示时，如果用户按了对话框上的某个键，系统将构造SkyEngine消息，通过mr_event函数传送给SkyEngine，消息类型为MR_DIALOG_EVENT，参数为该按键的ID。“确定”键ID为：MR_DIALOG_KEY_OK；“取消”键ID为：MR_DIALOG_KEY_CANCEL。

## 示例

```c
/*mrp code*/
int32 hDialog = 0;
hDialog = mrc_dialogCreate( (const
char*)SGL_LoadString(STR_DIALOG), (const char*)SGL_LoadString(STR_DIALOG),
MR_DIALOG_OK_CANCEL ); //STR_DIALOG字符串资源ID
//response the MR_DIALOG_EVENT
case
MR_DIALOG_EVENT:
{
if (wParam == MR_DIALOG_KEY_CANCEL)
{
//your
code
........
}
else if (wParam == MR_DIALOG_KEY_OK)
{
//your
code
........
}
}
```

## 相关

mr_dialogRelease
Copyright ?2005-20010 SKY-MOBI
