# mr_plat(1302) - 设置声音的大小

```c
int32 mr_plat(int32 code = 1302, int32 param)
```

## 说明

设置声音的大小。（播放时候的大小，非情景模式中的设置）。

## 参数

| 参数 | 说明 |
|---|---|
| param | Engine中音量等级） |

声音的大小（sky

## 返回值

MR_SUCCESS 成功
MR_FAILED 失败
MR_IGNORE 不支持该功能

## 示例

```c
/*mrp code*/
mrc_plat( 1302, 5 ); //set volum be 5.
```

## 相关

Copyright ?2005-20010 SKY-MOBI
