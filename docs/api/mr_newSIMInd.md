# mr_newSIMInd

```c
int32 mr_newSIMInd(int16 type, uint8* old_IMSI)
```

## 说明

用户SIM卡变更通知。

## 参数

| 参数 | 说明 |
|---|---|
| type | //未进行换卡操作，当前SkyEngine忽略该情况 |
| old_IMSI | 长度为16字节的旧IMSI号指针，若type为MR_SIM_NEW或MR_SIM_SAME，置为NULL |

MR_SIM_NEW,
//新手机第一次插入SIM卡
MR_SIM_CHANGE,
//用户更换SIM卡
MR_SIM_SAME

## 返回值

成功返回MR_SUCCESS, 失败返回MR_FAILED, 不关心返回MR_IGNORE。

## 备注

通知SkyEngine引擎，用户插入了新的SIM卡(包括第一次使用该手机和换卡操作)。当新手机插入SIM卡，或者用户进行换卡消息时，通知SkyEngine引擎进行备份。建议在短消息模块初始化完成后，调用该函数，确保该函数能正确执行。

## 相关

Copyright ?2005-20010 SKY-MOBI
