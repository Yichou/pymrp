# mr_editCreate

```c
int32 mr_editCreate(const char * title, const char * text, int32 type, int32 max_size)
```

## 说明

创建编辑框。

## 参数

| 参数 | 说明 |
|---|---|
| title | 编辑框的标题，unicode编码，网络字节序。 |
| text | 编辑框的初始内容，unicode编码，网络字节序。 |
| type | MR_EDIT_PASSWORD： 密码，用“*”显示 |
| max_size | 最多可以输入的字符（unicode）个数，这里每一个中文、字母、数字、符号都算一个字符。 |

输入法类型：
MR_EDIT_ANY：
任何字符
MR_EDIT_NUMERIC： 数字

## 返回值

&gt;0 为编辑框句柄，MR_FAILED表示失败.

## 备注

创建一个编辑框，并返回编辑框句柄。编辑框用来显示并提供用户编辑文字信息。text是编辑框显示的初始内容。
当编辑框显示时，如果用户选择了编辑框上的某个键，系统将构造SkyEngine消息，通过mr_event函数传送给SkyEngine，消息类型为MR_DIALOG_EVENT，参数为该按键的ID。“确定”键ID为：MR_DIALOG_KEY_OK；“取消”键ID为：MR_DIALOG_KEY_CANCEL。

## 示例

```c
/*mrp code*/
int32 hEdit = 0;
hEdit = mrc_editCreate( (const
char*)SGL_LoadString(STR_EDIT), (const char*)SGL_LoadString(STR_EDIT),
MR_DIALOG_OK_CANCEL, 100 ); //STR_EDIT为编辑框初始内容的资源ID
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

mr_editRelease
Copyright ?2005-20010 SKY-MOBI
