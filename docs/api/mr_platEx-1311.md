# mr_platEx(1311) - 获得base层的句柄

```c
int32 mr_platEx (int32 code = 1311, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得base层的句柄。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_LAYER_CREATE的指针 |
| input_len | T_LAYER_CREATE大小 |
| output | }T_DSM_COMMON_RSP; |
| output_len | T_DSM_COMMON_RSP大小 |
| cb | 无 |

指向
typedef struct
{
int32 p1;//层句柄
0是非法句柄

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 相关

Copyright ?2005-20010 SKY-MOBI
