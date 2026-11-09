# mr_findGetNext

```c
int32 mr_findGetNext(MR_SEARCH_HANDLE search_handle, char* buffer, uint32 len)
```

## 说明

取得一个目录搜索的结果。

## 参数

| 参数 | 说明 |
|---|---|
| search_handle | 调用mr_findStart时返回的查找句柄 |
| buffer | 缓冲区，用于存放查找成功时文件名或一级子目录名，GB编码 |
| len | 缓冲区大小 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

取得一个目录搜索的结果。将结果放置于buffer中。当目录中的结果都遍历过后，返回NULL。
这里需要注意的是，使用mr_findGetNext获得的子目录不能是“.”和“..”。

## 示例

```c
/*mrp code*/
int32 hFnd = 0;
char
buffer[60] = { 0 };
char buffer_fndGetNxt[60] = { 0 };
hFnd = mrc_findStart( "testDir", buffer,
sizeof(buffer) );
mrc_findGetNext( hFnd, buffer_fndGetNxt,
sizeof(buffer_fndGetNxt) );
```

## 相关

mr_findStart
mr_findStop
Copyright ?2005-20010 SKY-MOBI
