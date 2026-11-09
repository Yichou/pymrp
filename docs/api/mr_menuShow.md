# mr_menuShow

```c
int32 mr_menuShow(int32 menu)
```

## 说明

显示菜单。

## 参数

| 参数 | 说明 |
|---|---|
| menu | 菜单句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

显示菜单。当菜单显示时，如果用户选择了菜单上的某一项，系统将构造SkyEngine消息，通过mr_event函数传送给SkyEngine，消息类型为MR_MENU_SELECT，参数为该菜单项的index。如果用户选择了退出该菜单，系统将构造SkyEngine消息，通过mr_event函数传送给SkyEngine，消息类型为MR_MENU_RETURN。

## 示例

```c
/*mrp code*/
int32 hMenu = 0;
hMenu = mrc_menuCreate( (const
char*)SGL_LoadString(STR_MENU), 1 );
//STR_MENU字符串资源ID
mrc_menuSetItem( hMenu, (const
char*)SGL_LoadString(STR_MENU0), 0 );
//STR_MENU0字符串资源ID
mrc_menuShow(hMenu);
//response the MR_MENU_SELECT
case
MR_MENU_SELECT:
{
int32 index =
wParam; //the selected menu item index
//
your code
........
}
//response the MR_MENU_SELECT and MR_MENU_RETURN
case
MR_MENU_RETURN:
{
//your
code
.............
}
```

## 相关

mr_menuCreate
mr_menuSetItem
Copyright ?2005-20010 SKY-MOBI
