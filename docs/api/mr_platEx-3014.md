# mr_platEx(3014) - 绘制mtk资源格式的图片

```c
int32 mr_platEx (int32 code = 3014, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

绘制mtk资源格式的图片。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_DRAW_DIRECT_REQ数据结构指针 |
| input_len | T_DRAW_DIRECT_REQ数据结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE
不支持该功能

## 备注

输入数据结构：
typedef struct
{
char
*src;
int32 src_len;
int32 src_type;
int32
ox;
int32 oy;
int32
w;
int32 h;
}T_DRAW_DIRECT_REQ;

## 相关

Copyright ?2005-20010 SKY-MOBI
