# mr_platEx(1001) - 第二内存申请

```c
int32 mr_platEx (int32 code = 1001, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

第二内存申请。在某些内存紧张的平台中，sky
Engine尝试申请第二内存，第二内存与mr_mem_get获取的第一内存不必连续，以此方法解决某些平台内存紧张问题。若第二内存申请成功，将用于VM的屏幕缓冲，在128×160的平台上需要40K，在176×220的平台上需要76K。（一般返回lcd
buffer）。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 第二内存的地址 |
| output_len | 第二内存长度 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 相关

Copyright ?2005-20010 SKY-MOBI
