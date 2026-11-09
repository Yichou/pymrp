# mr_plat(2506) - 获得缩放等级

```c
int32 mr_plat(int32 code = 2506, int32 param)
```

## 说明

获得camera的缩放等级。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

缩放等级+ MR_PLAT_VALUE_BASE

## 示例

```c
/*mrp code*/
int32 zGrade = 0;
zGrade = mrc_plat( 2506, 0 );
mrc_printf(
"Zoom grade = %d.", (zGrade - MR_PLAT_VALUE_BASE) );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
