# mr_platEx(1208) - 设置手机铃声

```c
int32 mr_platEx (int32 code = 1208, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置手机铃声。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_DSM_RING_SET结构的指针。 |
| input_len | T_DSM_RING_SET 结构的大小 |
| output | 输出参数的起始地址 |
| output_len | 输出参数大小（字节数） |
| cb | 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源 |

## 返回值

MR_SUCCESS : 设置成功
MR_FAILED :
设置失败
MR_IGNOR : 不支持该功能

## 备注

数据结构：
pedef struct
{
int32 scene;
int32 type;
char
*path;
//gb编码 （相对VM当前目录的路径和歌曲名称）
}T_DSM_RING_SET;
Type：
0：MR_CALL_RING
（来电铃声）
1：MR_SMS_RING （短信提示音）
2：MR_ALARM_RING （闹钟提示音）
Scene：
0：MR_SCENE_NORMAL （一般模式）
1：MR_SCENE_MUTE
（静音模式）

## 相关

Copyright ?2005-20010 SKY-MOBI
