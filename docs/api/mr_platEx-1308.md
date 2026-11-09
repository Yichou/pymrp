# mr_platEx(1308) - 设置参与刷新的层

```c
int32 mr_platEx (int32 code = 1308, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置参与刷新的层的句柄的列表。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_BLT的指针 |
| input_len | T_BLT大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构：
typedef struct
{
int32 layer1;
int32
layer2;
int32 layer3;
int32
layer4;
}T_BLT;

## 相关

Copyright ?2005-20010 SKY-MOBI
