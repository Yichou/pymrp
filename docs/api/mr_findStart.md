# mr_findStart

```c
MR_SEARCH_HANDLE mr_findStart(const char* name, char* buffer, uint32 len)
```

## 说明

开始目录搜索。

## 参数

| 参数 | 说明 |
|---|---|
| name | 目录名 |
| buffer | 缓冲区，用于存放查找成功时第一个文件名或一级子目录名，GB编码 |
| len | 缓冲区大小 |

## 返回值

&gt;0 为返回的文件查找句柄，失败返回MR_FAILED.

## 备注

准备搜索name指定的目录，当dsm调用该函数后，系统初始化一个目录搜索，并返回第一个目录搜索的结果，每当dsm调用一次mr_findGetNext函数，系统返回下一个该目录下的文件或一级子目录名。该函数只返回查找句柄。当name为空字符串""时（注意name指向空串，但name不是NULL），搜索SkyEngine引擎的文件根目录。如：若手机以"/dsmdata/"作为SkyEngine引擎的文件根目录，当name为空字符串时，搜索目录"/dsmdata"。
例：一个目录下有文件：“a.bmp”、”b.mrp”和目录“data”，则mr_findStart返回查找句柄和“a.bmp”，紧接着的三次调用mr_findGetNext返回“b.mrp”、“data”和MR_FAILED。

## 示例

```c
/*mrp code*/
char buffer[60] = { 0
};
mrc_findStart( "testDir", buffer,
sizeof(buffer) );
```

## 相关

mr_findGetNext
mr_findStop
Copyright ?2005-20010 SKY-MOBI
