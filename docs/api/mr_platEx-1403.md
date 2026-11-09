# mr_platEx(1403) - 设置不要显示的文件类型

```c
int32 mr_platEx (int32 code = 1403, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置不要显示的文件类型。

## 参数

| 参数 | 说明 |
|---|---|
| input | *input 要显示的文件类型的宏值（见文件类型的宏值） |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 相关

Copyright ?2005-20010 SKY-MOBI
