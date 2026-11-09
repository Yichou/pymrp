# mr_getScreenInfo

```c
int32 mr_getScreenInfo(mr_screeninfo * screeninfo)
```

## 说明

获取屏幕信息。

## 参数

| 参数 | 说明 |
|---|---|
| screeninfo | 返回屏幕信息数据结构mr_screeninfo |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

获取屏幕宽、高、象素深度等信息。
mr_screeninfo格式如下：
typedef
struct
{
uint32
width;
//屏幕宽
uint32
height;
//屏幕高
uint32
bit;
//屏幕象素深度，单位bit，如：6万5千色（16bit色深）应该返回16。
}mr_screeninfo;

## 示例

```c
/*mrp code*/
mr_screeninfo info;
mrc_getScreenInfo( &amp;info );
mrc_printf(
"Screen info:width = %d, height = %d, bit = %d.", info.width, info.height,
info.bit );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
