# mr_platEx(1220) - 获得rom目录

```c
int32 mr_platEx (int32 code = 1220, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得rom目录。

## 参数

| 参数 | 说明 |
|---|---|
| input | 输入参数的起始地址 |
| input_len | 输入参数大小（字节数） |
| output | 根目录下的绝对路径。Gb编码。 比如 mulgame/mr/nes |
| output_len | 路径的长度 |
| cb | 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源 |

## 返回值

MR_SUCCESS ：成功
MR_FAILED ：失败
MR_IGNORE
: 不支持该功能

## 备注

用来获取厂商自己设置的nes放置rom的目录名称，不要带盘符，返回一个型如“game/nes”的绝对目录名。(目前nes会默认搜索本地U盘跟外插存储卡)。

## 相关

Copyright ?2005-20010 SKY-MOBI
