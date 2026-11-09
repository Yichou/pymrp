# mr_plat(101) - 设置旋转角度

```c
int32 mr_plat(int32 code = 101, int32 param)
```

## 说明

设置图象旋转显示的角度。

## 参数

| 参数 | 说明 |
|---|---|
| param | 7：MR_LCD_MIRROR_ROTATE_270 |

0：MR_LCD_ROTATE_NORMAL
1：MR_LCD_ROTATE_90
2：MR_LCD_ROTATE_180
3：MR_LCD_ROTATE_270
4：MR_LCD_MIRROR
5：MR_LCD_MIRROR_ROTATE_90
6：MR_LCD_MIRROR_ROTATE_180

## 返回值

MR_SUCCESS 设置成功, MR_FAILED 设置失败, MR_IGNORE 不支持该功能。

## 相关

Copyright ?2005-20010 SKY-MOBI
