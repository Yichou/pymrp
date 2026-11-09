# mr_platEx(3013)

```c
int32 mr_platEx (int32 code = 3013, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

MR_SET_ANIMATION_BLT_CB，未实现。

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
成功
MR_FAILED
失败
MR_IGNORE
不支持该功能

## 备注

Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下：
typedef
void (*MR_PLAT_EX_CB)(uint8* output, int32
output_len);
若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。

## 相关

Copyright ?2005-20010 SKY-MOBI
