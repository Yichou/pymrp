# mr_close

```c
int32 mr_close(MR_FILE_HANDLE f)
```

## 说明

关闭文件。

## 参数

| 参数 | 说明 |
|---|---|
| f | 要关闭的文件句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
MR_FILE_HANDLE fh;
fh = mrc_open( "testFile.txt",
MR_FILE_CREATE|MR_FILE_RDWR );
mrc_close( fh
);
```

## 相关

mr_open
Copyright ?2005-20010 SKY-MOBI
