# mr_mem_free

```c
int32 mr_mem_free (char* mem, uint32 mem_len)
```

## 说明

内存释放接口。

## 参数

| 参数 | 说明 |
|---|---|
| mem | 释放由mr_mem_get分配的内存 |
| mem_len | 内存大小，mr_mem_get返回的值 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 相关

mr_mem_get
Copyright ?2005-20010 SKY-MOBI
