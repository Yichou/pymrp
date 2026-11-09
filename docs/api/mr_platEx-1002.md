# mr_platEx(1002) - 释放申请到的第二内存

```c
int32 mr_platEx (int32 code = 1002, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

释放申请到的第二内存。

## 参数

| 参数 | 说明 |
|---|---|
| input | 第二内存的地址 |
| input_len | 第二内存长度 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。cb的输出参数是资源清理回调函数，函数的类型定义如下：
typedef
void (*MR_PLAT_EX_CB)(uint8* output, int32
output_len);
若移植层需要在mr_platEx函数返回后进行清理工作（比如output的内存是移植层动态申请的，需要VM层使用完后释放），可以给cb赋值，VM层在使用过output后，会调用cb。

## 相关

Copyright ?2005-20010 SKY-MOBI
