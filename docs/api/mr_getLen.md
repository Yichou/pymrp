# mr_getLen

```c
int32 mr_getLen(const char* filename)
```

## 说明

取得文件长度。

## 参数

| 参数 | 说明 |
|---|---|
| filename | 文件名 |

## 返回值

&gt;=0 为文件长度，MR_FAILED表示失败.

## 示例

```c
/*mrp code*/
mrc_getLen( "testFile.txt" );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
