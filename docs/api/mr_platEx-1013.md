# mr_platEx(1013) - 释放申请内部cache

```c
int32 mr_platEx (int32 code = 1013, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

释放申请内部cache。

## 参数

| 参数 | 说明 |
|---|---|
| input | 已经申请到的buffer的地址 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 相关

Copyright ?2005-20010 SKY-MOBI
