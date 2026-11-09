# mr_platEx(1307) - 获取SIM卡个数信息

```c
int32 mr_platEx (int32 code = 1307, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得sim卡个数等信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | MR_DUALSIM_SET_T结构的指针 |
| output_len | MR_DUALSIM_SET_T结构大小； |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

用来获取多卡多待手机当前的sim状态信息。如果是非多卡多待手机，可以直接返回MR_IGNORE；
数据结构：
typedef
struct
{
uint8 totalNum; //sim numbers, max to
6
uint8 curActive; //index of simId[] witch
actived
uint16 dummy; //no use, just for align
int32
simId[4]; //mapping to plat sim socket id
char*
simNamePtr[4]; //sim卡名字,unicode
uint16 simNameLen[4];
//名字长度
}MR_DUALSIM_SET_T;

## 相关

Copyright ?2005-20010 SKY-MOBI
