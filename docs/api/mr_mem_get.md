# mr_mem_get

```c
int32 mr_mem_get (char** mem_base, uint32* mem_len)
```

## 说明

内存申请函数。

## 参数

| 参数 | 说明 |
|---|---|
| mem_base | 返回的内存基地址 |
| mem_len | 返回的内存长度 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

当引擎正常启动时，引擎取得系统内存资源。该函数在SkyEngine引擎启动时只会调用一次，一次性取得所有需要的内存。在SkyEngine引擎启动之后，SkyEngine引擎会自己管理内存资源。

## 相关

mr_mem_free
Copyright ?2005-20010 SKY-MOBI
