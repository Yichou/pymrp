# mr_dialogRefresh

```c
int32 mr_dialogRefresh(int32 dialog, const char * title, const char * text, int32 type)
```

## 说明

刷新对话框。

## 参数

| 参数 | 说明 |
|---|---|
| dialog | 对话框的句柄 |
| title | 对话框的标题，unicode编码，网络字节序。 |
| text | 对话框内容，unicode编码，网络字节序。 |
| type | “取消”键。 |

若type为-1，表示type不变。
对话框类型：
MR_DIALOG_OK：对话框有“确定”键。
MR_DIALOG_OK_CANCEL：对话框有“确定”和“取消”键。
MR_DIALOG_CANCEL：对话框有

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
int32 hDialog = 0;
hDialog = mrc_dialogCreate( (const
char*)SGL_LoadString(STR_DIALOG), (const char*)SGL_LoadString(STR_DIALOG),
MR_DIALOG_OK_CANCEL ); //STR_DIALOG字符串资源ID
mrc_dialogRefresh(
hDialog, (const char*)SGL_LoadString(STR_DIALOGREFRESH), (const
char*)SGL_LoadString(STR_DIALOGREFRESH), MR_DIALOG_OK_CANCEL );
//STR_DIALOGREFRESH被刷新的字符串资源ID
```

## 相关

mrc_dialogCreate
Copyright ?2005-20010 SKY-MOBI
