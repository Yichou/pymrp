# mr_plat(1218) - 查询存储卡的状态

```c
int32 mr_plat(int32 code = 1218, int32 param)
```

## 说明

查询存储卡的状态。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

存储卡状态的枚举如下：
enum
{
MR_MSDC_NOT_EXIST =
MR_PLAT_VALUE_BASE,
MR_MSDC_OK,
MR_MSDC_NOT_USEFULL /*可能在usb模式导致无法操作t卡*/
};

## 示例

```c
/*mrp code*/
int32 GetTcardState(void)
{
return mrc_plat( 1218, 0
);
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
