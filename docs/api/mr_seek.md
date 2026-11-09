# mr_seek

```c
int32 mr_seek(MR_FILE_HANDLE f, int32 pos, int method)
```

## 说明

设置文件读写指针。

## 参数

| 参数 | 说明 |
|---|---|
| f | 文件句柄 |
| pos | 文件读写指针位置 |
| method | MR_SEEK_END, //从文件当前位置开始搜索； |

设置方式,可能的取值为：
MR_SEEK_SET,
//从文件头开始搜索；
MR_SEEK_CUR, //从文件尾开始搜索；

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
MR_FILE_HANDLE fh;
fh = mrc_open( "testFile.txt",
MR_FILE_RDWR );
mrc_seek( fh, 10, MR_SEEK_SET);
//从文件头开始搜索；
mrc_seek( fh, 0, MR_SEEK_END); //从文件尾开始搜索；
mrc_seek(
fh, 10, MR_SEEK_CUR); //从文件当前位置开始搜索；
mrc_close( fh
);
```

## 相关

mr_open
mr_close
Copyright ?2005-20010 SKY-MOBI
