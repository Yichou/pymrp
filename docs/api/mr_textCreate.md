# mr_textCreate

```c
int32 mr_textCreate(const char * title, const char * text, int32 type)
```

## 说明

建立文本框。

## 参数

| 参数 | 说明 |
|---|---|
| title | 文本框的标题，unicode编码，网络字节序。 |
| text | 文本框内容，unicode编码，网络字节序。 |
| type | “取消”键。 |

文本框类型：
MR_DIALOG_OK：文本框有“确定”键。
MR_DIALOG_OK_CANCEL：文本框有“确定”和“取消”键。
MR_DIALOG_CANCEL：文本框有

## 返回值

&gt;0 为对话框句柄，MR_FAILED表示失败.

## 备注

创建一个文本框，并返回文本框句柄。文本框用来显示只读的文字信息。文本框和对话框并没有本质的区别，仅仅是显示方式上的不同，在使用上它们的主要区别是：对话框的内容一般较短，文本框的内容一般较长，对话框一般实现为弹出式的窗口，文本框一般实现为全屏式的窗口。也可以将对话框和文本框用相同方式实现。
文本框和对话框的消息参数是一样的。当文本框显示时，如果用户选择了文本框上的某个键，系统将构造SkyEngine消息，通过mr_event函数传送给SkyEngine，消息类型为MR_DIALOG_EVENT，参数为该按键的ID。“确定”键ID为：MR_DIALOG_KEY_OK；“取消”键ID为：MR_DIALOG_KEY_CANCEL。

## 示例

```c
/*mrp code*/
int32 hText = 0;
hText = mrc_textCreate( (const
char*)SGL_LoadString(STR_TEXT), (const char*)SGL_LoadString(STR_TEXT),
MR_DIALOG_OK_CANCEL ); //STR_TEXT文本框显示字符串资源ID
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

mr_textRelease
Copyright ?2005-20010 SKY-MOBI
