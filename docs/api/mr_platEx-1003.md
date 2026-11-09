# mr_platEx(1003) - 绑定一个socket到本机端口

```c
int32 mr_platEx (int32 code = 1003, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

绑定一个socket到本机端口（udp）。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_bind_st 结构的指针 |
| input_len | mr_bind_st 结构的长度 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构：
typedef struct
{
int32 socket; //socket
句柄
int32 port;
//端口号
}mr_bind_st;。

## 相关

Copyright ?2005-20010 SKY-MOBI
