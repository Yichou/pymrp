# mr_winRelease

```c
int32 mr_winRelease(int32 win)
```

## 说明

释放窗体。

## 参数

| 参数 | 说明 |
|---|---|
| win | 可扩展窗体句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
mrc_winRelease( hExtWnd );
//hExtWnd为mrc_winCreate创建的句柄
```

## 相关

mr_winCreate
Copyright ?2005-20010 SKY-MOBI
