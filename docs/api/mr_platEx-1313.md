# mr_platEx(1313) - 设置层位置

```c
int32 mr_platEx (int32 code = 1313, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置层位置。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_LAYER_POS的指针 |
| input_len | T_LAYER_POS大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构：
typedef struct
{
int32 x;
int32
y;
}T_LAYER_POS;

## 相关

Copyright ?2005-20010 SKY-MOBI
