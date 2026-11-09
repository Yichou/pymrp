# mr_plat(1213) - 获得手机当前的情景模式

```c
int32 mr_plat(int32 code = 1213, int32 param)
```

## 说明

获得手机当前的情景模式。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

返回：MR_PLAT_VALUE_BASE+主题枚举值
typedef
enum
{
MR_SCENE_NORMAL,
MR_SCENE_MEETING,
MR_SCENE_INDOOR,
MR_SCENE_OUTDOOR,
MR_SCENE_MUTE
}T_DSM_SCENE;

## 相关

Copyright ?2005-20010 SKY-MOBI
