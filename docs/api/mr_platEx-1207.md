# mr_platEx(1207) - UNICODE 转 GB

```c
int32 mr_platEx (int32 code = 1207, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

unicode转gb。

## 参数

| 参数 | 说明 |
|---|---|
| input | Unicode字符串指针。//大端 |
| input_len | Unicode字符串长度，Unicode字符串以”\0\0”结尾，该值仅做参考。 |
| output | 返回的GB字符串缓冲 |
| output_len | 返回的GB字符串缓冲的长度。 |
| cb | 无 |

## 返回值

MR_SUCCESS ：转换成功
MR_FAILED ：转换失败
MR_IGNORE
：不支持该功能

## 备注

Unicode字符串到gb字符串的转换。Unicode字符串以”\0\0”结尾，输入的“Unicode字符串长度”从Mythroad传下，仅有参考价值。

## 相关

Copyright ?2005-20010 SKY-MOBI
