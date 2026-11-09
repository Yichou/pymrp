# mr_menuCreate

```c
int32 mr_menuCreate(const char * title, int16 num)
```

## 说明

创建菜单。

## 参数

| 参数 | 说明 |
|---|---|
| title | 菜单的标题，unicode编码，网络字节序。 |
| num | 菜单项的数目 |

## 返回值

&gt;0 为菜单句柄，MR_FAILED表示失败.

## 备注

创建一个菜单，并返回菜单句柄，title是菜单的标题。

## 示例

```c
/*mrp code*/
int32 hMenu = 0;
hMenu = mrc_menuCreate( (const
char*)SGL_LoadString(STR_MENU), 18 );
//STR_MENU字符串资源ID
```

## 相关

mr_menuShow
Copyright ?2005-20010 SKY-MOBI
