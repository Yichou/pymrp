# mr_platEx(1012) - 申请内部cache

```c
int32 mr_platEx (int32 code = 1012, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

申请内部cache。

## 参数

| 参数 | 说明 |
|---|---|
| input | 要申请的buffer的大小 |
| input_len | 无 |
| output | 申请到的buffer的指针 |
| output_len | 无 |
| cb | 无 |

## 返回值

一直返回MR_SUCCESS，需要判断*output的值, 未实现返回MR_IGNORE.

## 相关

Copyright ?2005-20010 SKY-MOBI
