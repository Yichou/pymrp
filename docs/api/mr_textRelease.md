# mr_textRelease

```c
int32 mr_textRelease(int32 text)
```

## 说明

释放文本框。

## 参数

| 参数 | 说明 |
|---|---|
| text | 文本框句柄 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 示例

```c
/*mrp code*/
mrc_textRelease( hText );
//hText为mrc_textCreate创建的句柄
```

## 相关

mr_textCreate
Copyright ?2005-20010 SKY-MOBI
