# mr_rename

```c
int32 mr_rename(const char* oldname, const char* newname)
```

## 说明

文件重命名。

## 参数

| 参数 | 说明 |
|---|---|
| oldname | 原文件名 |
| newname | 新文件名 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

这里有个需要特别注意的地方是，不在相同目录下的rename，这样的操作就相当于move，由于移植层没做特殊处理直接转掉平台的函数，所以就存在平台接口差异导致该接口表现不完全一致，目前在MTK上是可以带路径rename的，但展讯上不行。

## 示例

```c
/*mrp code*/
mrc_rename( "testFile.txt", "newtestFile.txt" );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
