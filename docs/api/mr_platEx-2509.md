# mr_platEx(2509) - 获取预览数据

```c
int32 mr_platEx (int32 code = 2509, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取预览数据。一旦调用该接口，则会获取预览数据，即使关闭了camera，任然在获取当前激活层的数据。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | T_LAYER_INFO数据结构指针地址 |
| output_len | T_LAYER_INFO数据结构大小 |
| cb | 无 |

## 返回值

MR_SUCCESS 成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 备注

typedef struct
{
int32
handle;
int32
w;
int32 h;
char
*buffer;
}T_LAYER_INFO;

## 示例

```c
/*mrp code*/
T_LAYER_INFO *pdata = NULL;
mrc_platEx( 2509, NULL, 0,
(uint8**)&amp;pdata, (int32*)&amp;len, NULL );
mrc_printf( "Get data:
data.Buffer = %d, data.height = %d, data.weight = %d",
pdata-&gt;buffer, pdata-&gt;h, pdata-&gt;w );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
