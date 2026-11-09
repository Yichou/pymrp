# mr_platEx(1017) - 获得信号强度

```c
int32 mr_platEx (int32 code = 1017, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得信号强度。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 指向T_RX 的指针 |
| output_len | T_RX结构大小 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.
注：需要调用mr_plat中的1016和1018进行初始化和退出

## 备注

数据结构：
typedef struct
{
uint8 level;
uint8
current_band;
uint8 rat;
uint8
flag;
}T_RX;。

## 相关

Copyright ?2005-20010 SKY-MOBI
