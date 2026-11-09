# mr_platEx(1201) - 获取字宽字高

```c
int32 mr_platEx (int32 code = 1201, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取字宽字高。这个接口主要为了解决某些平台字宽字高不等的情况。这个接口返回在该平台上最大的字宽和字高。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_IGNORE ： 不支持该功能
其他 ： 0～7bit 中文字宽
8～15bit
中文字高
16～23bit 英文字宽
24～31bit 英文字高

## 相关

Copyright ?2005-20010 SKY-MOBI
