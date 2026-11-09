# mr_plat(2703) - 停止

```c
int32 mr_plat(int32 code = 2703, int32 param)
```

## 说明

录音停止。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 示例

```c
/*mrp code*/
mrc_plat( 2703 , 0 );
```

## 相关

mr_platEx(2700)
Copyright ?2005-20010 SKY-MOBI
