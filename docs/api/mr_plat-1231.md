# mr_plat(1231) - 获得当前文件的指针的位置

```c
int32 mr_plat(int32 code = 1231, int32 param)
```

## 说明

获得当前文件的指针的位置。

## 参数

| 参数 | 说明 |
|---|---|
| param | 文件句柄 |

## 返回值

MR_PLAT_VALUE_BASE+指针实际位置

## 示例

```c
/*mrp code*/
int32 GetFilePointPos(int32 fh)
//fh为mrc_open打开的文件句柄
{
if (NULL ==
fh)
return MR_FAILED;
/*1231:get
file point pos*/
return mrc_plat( 1231, fh )
- MR_PLAT_VALUE_BASE;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
