# mr_dialogRelease

```c
int32 mr_dialogRelease(int32 dialog)
```

## 说明

释放对话框。

## 参数

| 参数 | 说明 |
|---|---|
| dialog | 对话框句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
mrc_dialogRelease( hDialog );
//hDialog为mrc_dialogCreate创建的句柄
```

## 相关

mr_dialogCreate
Copyright ?2005-20010 SKY-MOBI
