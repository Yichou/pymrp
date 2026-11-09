# mr_platEx(4011) - 电话本搜索

```c
int32 mr_platEx (int32 code = 4011, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

搜索电话本。

## 参数

| 参数 | 说明 |
|---|---|
| input | }T_MR_PHB_SEARCH_REQ; |
| input_len | T_MR_PHB_SEARCH_REQ结构大小 |
| output | }T_MR_PHB_SEARCH_RSP; |
| output_len | T_MR_PHB_SEARCH_RSP结构大小 |
| cb | 无 |

typedef struct
{
S8
pattern[MR_PHB_MAX_SEARCH_PATTERN]; /*搜索条件大端unicode*/
U16
search_type; /*搜索类型，1：通过名称；2：通过号码*/
U16
storage;
/*不关心*/
typedef struct
{
U16
index;
/*在列表中的位置，起始是 0*/
U16
store_index;
/*在sim卡或者手机中物理的位置*/
T_MR_PHB_ENTRY phb_entry;
/*具体信息*/

## 返回值

MR_PHB_NOT_READY /*电话本初始化中*/
MR_PHB_NOT_FOUND
//2种情况，1：搜索参数为空；2：未找到
MR_PHB_SUCCESS
//搜索成功

## 相关

Copyright ?2005-20010 SKY-MOBI
