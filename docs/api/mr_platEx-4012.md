# mr_platEx(4012) - 电话本编辑

```c
int32 mr_platEx (int32 code = 4012, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

修改，修改，添加电话本条目。

## 参数

| 参数 | 说明 |
|---|---|
| input | 注：当具体信息中的号码和名称为空的时候表示要删除index指向的那个条目 |
| input_len | T_MR_PHB_SET_ENTRY_REQ结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

typedef struct
{
U16
storage;//信息存储的位置，sim卡，还是手机
U16 index;
//要修改的条目在列表中的索引（0开始），如果是0xfffff表示增加一个条目
T_MR_PHB_ENTRY entry;
//具体的信息
}T_MR_PHB_SET_ENTRY_REQ;

## 返回值

MR_PHB_SUCCESS：请求已经发出
MR_PHB_ERROR
请求发送失败
注：这个操作是一个异步的过程，操作的结构会通过mr_event的形式上送。
具体看最后的事件说明.

## 相关

Copyright ?2005-20010 SKY-MOBI
