# mr_save_mrp

```c
int32 mr_save_mrp(void *p, uint32 l)
```

## 说明

文件下载判断与保存。

## 参数

| 参数 | 说明 |
|---|---|
| p | 下载内容指针，指向保存下载文件内容的地址 |
| l | 下载内容长度 |

## 返回值

当下载的是skyengine的应用，并保存成功，返回MR_SUCCESS, 如果保存失败返回MR_FAILED.
如下载的是非skyengine应用，返回MR_IGNORE.

## 备注

对下载内容（保存在内存区中的一个下载的文件）进行判断，若下载文件是SkyEngine应用，由SkyEngine引擎对下载文件进行保存。使用本函数时，下载文件应该已经下载完全，并且全部内容保存在所给的内存中。

## 相关

Copyright ?2005-20010 SKY-MOBI
