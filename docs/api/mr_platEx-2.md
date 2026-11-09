# mr_platEx(2) - 设置菜单项

```c
int32 mr_platEx (int32 code = 2, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置菜单项。

## 参数

| 参数 | 说明 |
|---|---|
| input | MMIMR_LISTBOXITEM_T 结构的指针 |
| input_len | MMIMR_LISTBOXITEM_T 结构的大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

设置单/多选list中的item (调用创建接口后 调用这个接口)
数据结构：
typedef struct
{
int32 menu; //list的句柄
char
*text; //这一项的名称(大端unicode)
int32
index; //这一项在整个list中的位置(从0开始)
int32 selected;
//这一项是否标记为选中(1：选中；0：未选中)
}MMIMR_LISTBOXITEM_T;。

## 示例

```c
/*mrp code*/
MMIMR_LISTBOXITEM_T listItem = { 0 };
listItem.index =
0;
listItem.menu = hMenu; //mrc_platEx(1)创建的菜单句柄
listItem.selected
= 0;
listItem.text = (char*)SGL_LoadString(STR_MENU0）；
mrc_platEx( 2,
(uint8*)&amp;listItem, sizeof(MMIMR_LISTBOXITEM_T), NULL, NULL, NULL
);
```

## 相关

mr_platEx(1)
Copyright ?2005-20010 SKY-MOBI
