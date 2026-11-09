# mr_platEx(3005) - 释放gif解码资源

```c
int32 mr_platEx (int32 code = 3005, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

应用通知移植层释放先前gif解码（mr_platEx（3004））用到的资源。

## 参数

| 参数 | 说明 |
|---|---|
| input | MRAPP_GIF_HEADER数据结构指针（mr_platEx（3004）返回的指针） |
| input_len | MRAPP_GIF_HEADER数据结构大小 |
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

## 示例

```c
/*mrp code*/
MRAPP_GIF_HEADER *decodeRsp;
//由mr_platEx(3004)得到
mrc_platEx( 3005, (uint8*)decodeRsp,
sizeof(MRAPP_GIF_HEADER), NULL, NULL, NULL );
```

## 相关

mr_platEx(3004)
Copyright ?2005-20010 SKY-MOBI
