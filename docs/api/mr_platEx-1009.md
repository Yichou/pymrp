# mr_platEx(1009) - 设置墙纸

```c
int32 mr_platEx (int32 code = 1009, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置墙纸。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_SET_IDLE_PAPER_REQ数据结构 |
| input_len | T_SET_IDLE_PAPER_REQ 的大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_WAITING : 请求成功
MR_FAILED : 请求失败
MR_IGNORE :
不支持该功能

## 备注

数据结构如下，
typedef struct
{
int32 setType;/* MR_IDLE_BG_PAPER
墙纸，MR_IDLE_SAVER_PAPER屏保*/
U8
*filename;/*图片的相对路径*/
}T_SET_IDLE_PAPER_REQ;

## 相关

Copyright ?2005-20010 SKY-MOBI
