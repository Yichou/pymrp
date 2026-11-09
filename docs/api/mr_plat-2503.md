# mr_plat(2503) - 恢复

```c
int32 mr_plat(int32 code = 2503, int32 param)
```

## 说明

恢复camera到preview状态。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_SUCCESS 成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 示例

```c
/*mrp code*/
mrc_plat( 2503, 0 );
```

## 相关

mr_plat(2502)
Copyright ?2005-20010 SKY-MOBI
