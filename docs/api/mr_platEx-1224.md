# mr_platEx(1224) - 获取小区ID

```c
int32 mr_platEx (int32 code = 1224, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取小区ID等部分信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 指向T_DSM_CELL_INFO 的指针 |
| output_len | T_DSM_CELL_INFO结构大小 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构：
typedef struct
{
uint16
lac;
uint16
cell_id;
uint8 mnc[2];
uint8 mcc[3];
uint8
mnc3[4];/*移植版本x15x后增加的字段，mnc3[0]中表示的mnc的第三位*/
}T_DSM_CELL_INFO;
注：需要调用mr_plat中的1215和1216进行初始化和退出

## 相关

Copyright ?2005-20010 SKY-MOBI
