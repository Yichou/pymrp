# mr_plat(1391) - 查询是否支持后台接口

```c
int32 mr_plat(int32 code = 1391, int32 param)
```

## 说明

查询移植层是否支持后台运行接口。

## 参数

| 参数 | 说明 |
|---|---|
| param | appid |

## 返回值

MR_SUCCESS 表示支持
MR_FAILED 不支持
MR_IGNORE 不支持该功能

## 备注

如果该移植版本支持后台运行，那么返回的是MR_SUCCESS 。当前版本没有进行任何的条件判断；

## 示例

```c
/*mrp
code*/
int32 GetBackStageSupport(int32 appid)
{
int32 ret =
mrc_plat(1391,appid);
return ret;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
