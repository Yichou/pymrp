# mr_platEx(3009) - DMA异步刷屏

```c
int32 mr_platEx (int32 code = 3009, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

直接刷屏（非阻塞形式)。

## 参数

| 参数 | 说明 |
|---|---|
| input | 显示缓冲 |
| input_len | 缓冲大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED 失败
MR_IGNORE
不支持该功能

## 示例

```c
/*mrp code*/
uint16* lcdBuf = NULL;
lcdBuf =
(uint16*)w_getScreenBuffer();
//获取屏幕缓冲buffer
mrc_platEx( 3009, (uint8* )lcdBuf, 0, NULL, NULL, NULL
);
```

## 相关

Copyright ?2005-20010 SKY-MOBI
