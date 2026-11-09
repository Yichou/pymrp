# mr_plat(1006) - 隐藏状态栏上的图标

```c
int32 mr_plat(int32 code = 1006, int32 param)
```

## 说明

停止在idle上显示图标或者idle背景。

## 参数

| 参数 | 说明 |
|---|---|
| param | 应用编号 |

## 返回值

MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。

## 示例

```c
/*mrp code*/
int32 HideStateIcon(int32
appid)
{
int32 ret =
mrc_plat(1006,appid);
return
ret;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
