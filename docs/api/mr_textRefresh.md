# mr_textRefresh

```c
int32 mr_textRefresh(int32 handle, const char * title, const char * text)
```

## 说明

刷新文本框。

## 参数

| 参数 | 说明 |
|---|---|
| handle | 文本框的句柄 |
| title | 文本框的标题，unicode编码，网络字节序。 |
| text | 文本框内容，unicode编码，网络字节序。 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
int32 hText = 0;
hText = mrc_textCreate( (const
char*)SGL_LoadString(STR_TEXT), (const char*)SGL_LoadString(STR_TEXT),
MR_DIALOG_OK_CANCEL ); //STR_TEXT文本框显示字符串资源ID
mrc_textRefresh( hText,
(const char*)SGL_LoadString(STR_TEXTREFRESH), (const
char*)SGL_LoadString(STR_TEXTREFRESH) );
//STR_TEXTREFRESH文本框被刷新显示的字符串资源ID
```

## 相关

mr_textCreate
Copyright ?2005-20010 SKY-MOBI
