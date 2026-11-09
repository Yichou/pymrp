# mr_plat(4005) - 动感芯片进入监听晃动的模式

```c
int32 mr_plat(int32 code = 4005, int32 param)
```

## 说明

设置动感芯片监听倾斜模式。

## 参数

| 参数 | 说明 |
|---|---|
| param | 无 |

## 返回值

MR_SUCCESS 成功
MR_FAILED 失败
MR_IGNORE 不支持该功能

## 备注

晃动的值将通过mr_event值来传递
mr_event(p1,p2,p3);
p1:
MR_MOTION_EVENT(18)
p2:
MR_MOTION_EVENT_SHAKEA(1)
p3:指向这个数据结构的指针：
typedef
struct
{
int32 x;
//重力加速速度在x方向的分量
int32 y;
//重力加速速度在y方向的分量
int32 z;
//重力加速速度在z方向的分量
}T_MOTION_ACC;

## 相关

Copyright ?2005-20010 SKY-MOBI
