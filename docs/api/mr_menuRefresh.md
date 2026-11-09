# mr_menuRefresh

```c
int32 mr_menuRefresh(int32 menu)
```

## 说明

刷新菜单。

## 参数

| 参数 | 说明 |
|---|---|
| menu | 菜单句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
mrc_menuRefresh( hMenu ); //hMenu为mrc_menuCreate创建的句柄
```

## 相关

mr_menuCreate
Copyright ?2005-20010 SKY-MOBI
