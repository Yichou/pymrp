# mr_platEx(1008) - 调用mtk的发送短信界面

```c
int32 mr_platEx (int32 code = 1008, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

调用mtk的发送短信界面。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向T_PLAT_SENDSMS_REQ 数据结构 |
| input_len | T_PLAT_SENDSMS_REQ 的大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构如下，
typedef struct
{
char
*pNum;/*目前没有使用该参数*/
char
*pContent;/*大端unicode*/
}T_PLAT_SENDSMS_REQ;。

## 相关

Copyright ?2005-20010 SKY-MOBI
