# mr_platEx(3007) - 绘制BUFFER

```c
int32 mr_platEx (int32 code = 3007, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

绘制BUFFER。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED 失败
MR_IGNORE
不支持该功能

## 备注

case
MR_DRAW_BUFFER:
{
gdi_enable_non_block_blt();
GDI_LAYER_SET_FLAG(gdi_act_layer,GDI_LAYER_FLAG_FROZEN);
gdi_layer_blt_previous(0,0,
GDI_LAYER.width-1,GDI_LAYER.height-1);
GDI_LAYER_CLEAR_FLAG(gdi_act_layer,GDI_LAYER_FLAG_FROZEN);
return MR_SUCCESS;
}

## 相关

Copyright ?2005-20010 SKY-MOBI
