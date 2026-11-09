# mr_platEx(3008) - 获取ACTIVE LAYER

```c
int32 mr_platEx (int32 code = 3008, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取active layer。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | gdi_layer_struct数据结构指针 |
| output_len | gdi_layer_struct数据结构大小 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE
不支持该功能

## 备注

typedef struct gdi_layer_struct
{
U32
id;
U32 flag;
S32 layer_size; /*
bytes */
U16 width, height;
S16
clipx1, clipy1, clipx2, clipy2;
U8
*buf_ptr;
U8 *buf_ptr1;
gdi_rect_struct clips[GDI_LAYER_CLIP_STACK_COUNT];
U8
bits_per_pixel;
U8 clips_top;
U8
cf; /* real color format
( it will support LCD color format) */
U8
vcf; /* virtual color format
(convert to standard color format) */
gd_get_pixel_func
get_pixel;
gd_put_pixel_func
put_pixel;
struct gdi_layer_struct
*child;
struct gdi_layer_struct
*sib;
S32 offset_x, offset_y;
S32
offset_x_from_parent;
S32
offset_y_from_parent;
void
(*lazy_free_callback)(gdi_handle handle);
gdi_color
background; /* only valide when this layer is the "lowest" layer.
*/
U8 rotate_value;
}
gdi_layer_struct;

## 相关

Copyright ?2005-20010 SKY-MOBI
