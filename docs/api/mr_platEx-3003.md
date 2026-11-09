# mr_platEx(3003) - 查询解码状态

```c
int32 mr_platEx (int32 code = 3003, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

取得图像解码状态（异步解码）。未实现。

## 参数

| 参数 | 说明 |
|---|---|
| input | 输入参数的起始地址 |
| input_len | 输入参数大小（字节数） |
| output | 输出参数的起始地址 |
| output_len | 输出参数大小（字节数） |
| cb | 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源 |

## 返回值

MR_SUCCESS
解码成功
MR_FAILED
解码失败
MR_WAITING
正在解码
MR_IGNORE
不支持该功能

## 相关

Copyright ?2005-20010 SKY-MOBI
