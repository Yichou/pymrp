# mr_findStop

```c
int32 mr_findStop(MR_SEARCH_HANDLE search_handle)
```

## 说明

结束目录查找。

## 参数

| 参数 | 说明 |
|---|---|
| search_handle | 查找句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
int32 hFnd = 0;
char buffer[60] = { 0
};
hFnd = mrc_findStart( "testDir",
buffer, sizeof(buffer) );
mrc_findStop(
hFnd );
```

## 相关

mr_findStart
Copyright ?2005-20010 SKY-MOBI
