# mr_printf

```c
void mr_printf(const char *format, ...)
```

## 说明

调试信息打印。

## 参数

| 参数 | 说明 |
|---|---|
| format | 格式化字符串 |

## 返回值

无返回值.

## 示例

```c
/*mrp code*/
int32 width = 100, height = 1000, bit = 16;
mrc_printf( "Screen
info:width = %d, height = %d, bit = %d.", width, height, bit );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
