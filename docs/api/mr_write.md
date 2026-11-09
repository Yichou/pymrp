# mr_write

```c
int32 mr_write(MR_FILE_HANDLE f, void *p, uint32 l)
```

## 说明

写文件。

## 参数

| 参数 | 说明 |
|---|---|
| f | 文件句柄 |
| p | 待写入数据存放地址 |
| l | 待写入数据长度 |

## 返回值

&gt; 0 表示实际写入的字节数，失败返回MR_FAILED.

## 备注

初始化SkyEngine引擎，并运行指定的应用。当SkyEngine引擎启动时会调用mr_mem_get获取引擎需要的内存。
mr_mem_get函数由移植者实现，以取得引擎需要的内存。entry是SkyEngine入口参数。

## 示例

```c
/*mrp code*/
MR_FILE_HANDLE fh;
char buffer[60] = "Hello sky!";
fh =
mrc_open( "testFile.txt", MR_FILE_RDWR );
//可读写方式打开文件testFile.txt
mrc_write( fh, (void*)buffer,
sizeof(buffer) );
mrc_close( fh );
```

## 相关

mr_open
mr_close
Copyright ?2005-20010 SKY-MOBI
