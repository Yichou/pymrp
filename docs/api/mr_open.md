# mr_open

```c
MR_FILE_HANDLE mr_open(const char* filename, uint32 mode)
```

## 说明

打开文件。

## 参数

| 参数 | 说明 |
|---|---|
| filename | 文件名 |
| mode | 打开方式 |

## 返回值

当打开成功的时候，返回非空的文件句柄，如果失败返回NULL.

## 备注

mode取值:
MR_FILE_RDONLY
//以只读的方式打开文件。
MR_FILE_WRONLY
//以只写的方式打开文件。（可以将这个方式实现为与MR_FILE_RDWR相同的操作）
MR_FILE_RDWR
//以读写的方式打开文件。
MR_FILE_CREATE
//如果文件不存在，创建该文件，该参数不会单独出现，只能与其他值一同出现（使用“或”运算）
MR_FILE_RECREATE
//无论文件存不存在，都重新创建该文件，该参数不会单独出现，只能与其他值一同出现（使用“或”运算）
mode可能的取值：
a、 前三个参数的其中一个
b、 MR_FILE_WRONLY、MR_FILE_RDWR和MR_FILE_CREATE的“或”值
c、 MR_FILE_WRONLY、MR_FILE_RDWR和MR_FILE_RECREATE的“或”值

## 示例

```c
/*mrp code*/
MR_FILE_HANDLE fh;
fh = mrc_open( "testFile.txt",
MR_FILE_CREATE|MR_FILE_RDWR ); //创建可读写文件testFile.txt
fh =
mrc_open( "testFile.txt", MR_FILE_CREATE|MR_FILE_WRONLY );
//创建可写文件testFile.txt
fh = mrc_open( "testFile.txt",
MR_FILE_RECREATE|MR_FILE_WRONLY ); //重新创建可写文件testFile.txt
fh =
mrc_open( "testFile.txt", MR_FILE_CREATE|MR_FILE_RDWR
); //重新创建可读写文件testFile.txt
fh = mrc_open( "testFile.txt",
MR_FILE_WRONLY ); //以只写的方式打开文件testFile.txt
mrc_close( fh
);
```

## 相关

mr_close
Copyright ?2005-20010 SKY-MOBI
