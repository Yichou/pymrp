# mr_platEx(2505) - 拍照

```c
int32 mr_platEx (int32 code = 2505, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

拍照。

## 参数

| 参数 | 说明 |
|---|---|
| input | 2：单拍，需要调用mr_plat(2503)重新进入preview状态。 |
| input_len | sizeof(int32) |
| output | T_DSM_COMMON_RSP数据结构指针地址 |
| output_len | T_DSM_COMMON_RSP数据结构大小 |
| cb | 无 |

指向是否连拍的标志。
*input的值：
1：连拍；

## 返回值

MR_SUCCESS 成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 备注

数据结构如下：
typedef struct
{
int32
p1; /*图片buffer*/
int32
p2; /*图片大小*/
}T_DSM_COMMON_RSP;

## 示例

```c
/*mrp code*/
uint8 mode = 0;
int32 len = 0；
T_DSM_COMMON_RSP *photo =
NULL;
mrc_platEx( 2505, (uint8*)&amp;mode, sizeof (mode),
(uint8**)&amp;photo, (int32*)&amp;len， NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
