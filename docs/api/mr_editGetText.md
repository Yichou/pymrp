# mr_editGetText

```c
const char* mr_editGetText(int32 edit)
```

## 说明

获取编辑框内容。

## 参数

| 参数 | 说明 |
|---|---|
| edit | 编辑框句柄 |

## 返回值

返回编辑框内容的起始地址(编辑框的内容指针，大端unicode编码)，如果失败返回NULL.

## 备注

获取编辑框内容，unicode编码。调用该函数后，SkyEngine平台会在平台内部建立一个内容的备份，调用者不需保证在编辑框释放后内容仍然有效。该函数会在编辑框释放之前调用。

## 示例

```c
/*mrp code*/
const char *wstr = NULL;
wstr = mrc_editGetText( hEdit );
//hEdit为mrc_editCreate创建的句柄
```

## 相关

mr_editCreate
Copyright ?2005-20010 SKY-MOBI
