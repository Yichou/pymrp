# mr_platEx(1117) - 获取硬件版本号

```c
int32 mr_platEx (int32 code = 1117, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取硬件版本号。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 版本好字符串 |
| output_len | 字符串长度+1 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 相关

Copyright ?2005-20010 SKY-MOBI
