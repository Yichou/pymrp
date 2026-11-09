# mr_platEx(4016) - 获取条目信息

```c
int32 mr_platEx (int32 code = 4016, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得电话本中的指定一个条目的信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | 是相对于具体的存储位置而言的，不是在列表中的位置 |
| input_len | T_MR_PHB_GET_ENTRY_REQ结构大小 |
| output | }T_MR_PHB_GET_ENTRY_RSP; |
| output_len | T_MR_PHB_GET_ENTRY_RSP大小 |
| cb | 无 |

typedef struct
{
U16
index; //条目在列表中的索引
U16
storage;
//条目保存的位置。
}T_MR_PHB_GET_ENTRY_REQ;
注：此处的index
typedef struct
{
T_MR_PHB_ENTRY
entry;//本条目的具体信息

## 返回值

MR_PHB_OUT_OF_INDEX：索引越界
MR_PHB_SUCCESS
：读取成功
MR_PHB_NOT_READY /*电话本初始化中*/

## 相关

Copyright ?2005-20010 SKY-MOBI
