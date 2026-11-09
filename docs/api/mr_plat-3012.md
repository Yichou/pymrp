# mr_plat(3012) - 停止动画

```c
int32 mr_plat(int32 code = 3012, int32 param)
```

## 说明

动画停止。

## 参数

| 参数 | 说明 |
|---|---|
| param | mr_platEx(3011)得到的句柄 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE
不支持该功能

## 示例

```c
/*mrp code*/
T_DSM_COMMON_RSP *drawRes;
//由mr_platEx(3011)得到
mrc_plat( 3012, drawRes-&gt;p1);
```

## 相关

mr_platEx(3011)
Copyright ?2005-20010 SKY-MOBI
