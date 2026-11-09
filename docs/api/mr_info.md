# mr_info

```c
int32 mr_info(const char* filename)
```

## 说明

获取文件属性。

## 参数

| 参数 | 说明 |
|---|---|
| filename | 文件名 |

## 返回值

返回取值如下.
#define MR_IS_FILE 1//是文件
#define
MR_IS_DIR 2//是目录
#define MR_IS_INVALID
8//文件不存在，或既不是文件也不是目录

## 示例

```c
/*mrp code*/
int32 state;
state = mrc_fileState( "testFile.txt"
);
```

## 相关

Copyright ?2005-20010 SKY-MOBI
