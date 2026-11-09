# mr_platEx(1203) - 发送彩信

```c
int32 mr_platEx (int32 code = 1203, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

调用发送彩信功能。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_mms_st结构指针 |
| input_len | mr_mms_st结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

typedef struct
{
char*
addr;
//接收地址指针,ASCII
uint16* content;
//预设内容指针，大端unicode
}mr_mms_st;

## 相关

Copyright ?2005-20010 SKY-MOBI
