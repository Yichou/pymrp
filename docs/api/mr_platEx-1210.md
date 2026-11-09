# mr_platEx(1210) - 获取NES模拟器按键布局

```c
int32 mr_platEx (int32 code = 1210, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取NES模拟器按键布局。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | mr_nes_keys_st结构的指针 |
| output_len | mr_nes_keys_st结构长度 |
| cb | 无 |

## 返回值

MR_SUCCESS : 成功
MR_FAILED : 失败
MR_IGNORE :
不支持该功能

## 备注

数据结构：
typedef struct
_mr_nes_keys_st
{
uint8 k_up;
uint8 k_down;
uint8 k_left;
uint8
k_right;
uint8 k_se;
uint8 k_st;
uint8 k_a;
uint8 k_b;
uint8
auto_a;
uint8 auto_b;
}mr_nes_keys_st;

## 相关

Copyright ?2005-20010 SKY-MOBI
