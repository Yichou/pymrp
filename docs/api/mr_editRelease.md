# mr_editRelease

```c
int32 mr_editRelease(int32 edit)
```

## 说明

释放编辑框。

## 参数

| 参数 | 说明 |
|---|---|
| edit | 编辑框句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
mrc_editRelease( hEdit ); //hEdit为mrc_editCreate创建的句柄
```

## 相关

mr_editCreate
Copyright ?2005-20010 SKY-MOBI
