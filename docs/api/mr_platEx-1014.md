# mr_platEx(1014) - 申请扩展内存

```c
int32 mr_platEx (int32 code = 1014, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

申请扩展内存。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 要申请的buffer的大小 |
| output | 申请到的buffer的指针 |
| output_len | 申请到的内存的大小（和input_len相等） |
| cb | 无 |

## 返回值

一直返回成功，需要判断*output的值.

## 备注

这个函数管理了2个屏幕大小的buffer，但是这个buffer在切面切换，或者被pause的时候需要主动释放掉。

## 相关

Copyright ?2005-20010 SKY-MOBI
