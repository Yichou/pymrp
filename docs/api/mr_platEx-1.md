# mr_platEx(1) - 创建一个单/多选菜单

```c
int32 mr_platEx (int32 code = 1, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

建一个单/多选list。

## 参数

| 参数 | 说明 |
|---|---|
| input | MMIMR_LISTBOXSELECT_T结构指针 |
| input_len | MMIMR_LISTBOXSELECT_T结构的大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_FAILED ：创建对象失败
其他
：创建成功的对象的句柄.

## 备注

数据结构：
typedef struct
{
char *title;
//标题(大端unicode 编码)
int16 itemNum; //list 的项目个数
int16
listType; //如下
}MMIMR_LISTBOXSELECT_T;
listType
的值：
0：MR_LIST_NO_ICON (没有显示序号的)
1：MR_LIST_NORMAL_ICON
(一般的list的，建议调用menu的接口来实现)
2：MR_LIST_SINGLE_SEL
(单选框)
3：MR_LIST_MUTI_SEL (多选框)

## 示例

```c
/*mrp code*/
MMIMR_LISTBOXSELECT_T list = { 0 };
int32 hMenu = 0;
list.itemNum
= 18;
list.listType = MR_LIST_NO_ICON;
list.title =
(char*)SGL_LoadString( STR_MENU );
hMenu = mrc_platEx( 1,
(uint8*)&amp;list, sizeof(MMIMR_LISTBOXSELECT_T), NULL, NULL, NULL
);
```

## 相关

mr_platEx(2)
mr_menuShow
mr_menuRelease
Copyright ?2005-20010 SKY-MOBI
