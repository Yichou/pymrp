# mr_platEx(4032) - 获取电话本条数

```c
int32 mr_platEx (int32 code = 4032, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得电话本的条数。

## 参数

| 参数 | 说明 |
|---|---|
| input | }T_MR_PHB_GET_COUNT_REQ; |
| input_len | T_MR_PHB_GET_COUNT_REQ大小 |
| output | }T_MR_PHB_GET_COUNT_RSP; |
| output_len | T_MR_PHB_GET_COUNT_RSP大小 |
| cb | 无 |

typedef struct
{
int32 storage;
/*1：sim卡电话本；2：手机电话本；3；全部*/
typedef struct
{
int32
count;/*记录的个数*/

## 返回值

MR_PHB_SUCCESS
获得记录成功
MR_PHB_NOT_READY 电话本初始化中
MR_PHB_NOT_SUPPORT
输入参数错误

## 相关

Copyright ?2005-20010 SKY-MOBI
