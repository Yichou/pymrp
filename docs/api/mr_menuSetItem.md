# mr_menuSetItem

```c
int32 mr_menuSetItem(int32 menu, const char *text, int32 index)
```

## 说明

设置菜单项。

## 参数

| 参数 | 说明 |
|---|---|
| menu | 菜单句柄 |
| text | 菜单项的名字，使用unicode编码，网络字节序。 |
| index | 菜单项的index号，从0开始 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

在菜单里设置一个菜单项，参数index是该菜单项的序号，当用户选中某个菜单项时，把index号通过mr_event函数发送到SkyEngine中。

## 示例

```c
/*mrp code*/
int32 hMenu =
0;
hMenu = mrc_menuCreate( (const char*)SGL_LoadString(STR_MENU), 18
); //STR_MENU字符串资源ID
mrc_menuSetItem( hMenu, (const
char*)SGL_LoadString(STR_MENU0), 0 );
//STR_MENU0字符串资源ID
```

## 相关

mr_menuCreate
Copyright ?2005-20010 SKY-MOBI
