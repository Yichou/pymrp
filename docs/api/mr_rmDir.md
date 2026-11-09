# mr_rmDir

```c
int32 mr_rmDir(const char* name)
```

## 说明

删除目录。

## 参数

| 参数 | 说明 |
|---|---|
| name | 目录名 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

删除的文件夹必须为空。

## 示例

```c
/*mrp code*/
mrc_rmDir( "testDir" );
```

## 相关

mr_mkDir
Copyright ?2005-20010 SKY-MOBI
