# mr_platEx(4042) - 获得选中记录信息

```c
int32 mr_platEx (int32 code = 4042, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得选中的一个电话本记录的信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | T_MR_PHB_ENTRY 结构指针 |
| output_len | T_MR_PHB_ENTRY 结构大小 |
| cb | 无 |

## 返回值

MR_SUCCESS ：获得信息成功
MR_FAILED ：获得信息失败
MR_IGNORE
：不支持该功能
注：选中还是返回的操作将由MR_LOCALUI_EVENT（10）
事件传递给VM
0：MR_LOCALUI_OK
（表示用户选择了一个文件）
1：MR_LOCALUI_CANCEL（表示用户选择退出浏览这个功能）

## 备注

数据结构：
#define MR_PHB_MAX_NAME (36*2)
#define
MR_PHB_MAX_NUMBER (48*2)
#define
MR_PHB_MAX_SEARCH_PATTERN (60*2)
typedef struct
{
S8 name[MR_PHB_MAX_NAME];
S8 number[MR_PHB_MAX_NUMBER];
S8 homeNumber[MR_PHB_MAX_NUMBER];
S8 officeNumber[MR_PHB_MAX_NUMBER];
S8 faxNumber[MR_PHB_MAX_NUMBER];
S8 emailAddress[MR_PHB_MAX_NUMBER];
}T_MR_PHB_ENTRY;

## 相关

Copyright ?2005-20010 SKY-MOBI
