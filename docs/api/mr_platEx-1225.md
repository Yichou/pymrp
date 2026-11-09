# mr_platEx(1225) - 获取手柄信息

```c
int32 mr_platEx (int32 code = 1225, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取手柄信息。

## 参数

| 参数 | 说明 |
|---|---|
| input | MRAPP_HANDLE_CODE_T结构的指针。 |
| input_len | MRAPP_HANDLE_CODE_T结构的大小 |
| output | 指向MRAPP_HANDLE_INFO_T 的指针 |
| output_len | MRAPP_HANDLE_INFO_T结构大小 |
| cb | 回调函数，由移植层返回给应用，如果应用成发现这个返回值为非空，那么需要在使用完返回数据后调用这个cb函数来释放移植层分配的资源 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构：
typedef
struct
{
uint32 state; //手柄标志，目前使用
//0
bit：手柄状态，0手柄未插入；
//
1手柄已插入。
uint8 k_up; //按键上，当值为：0 未按下， 1 按下，
下同
uint8 k_down; //按键下
uint8
k_left; //按键左
uint8 k_right; //按键右
uint8 k_select; //按键 “选择”
uint8 k_start;
//按键 “开始”
uint8 k_a; //按键
A
uint8 k_b; //按键 B
uint8 k_auto_a; //按键 自动A
uint8 k_auto_b; //按键
自动B
uint8 k_c; //按键
其他，保留
uint8 k_d; //按键 其他，保留
uint8 k_left_up; //按键 左上
uint8 k_left_down; //按键 左下
uint8 k_right_down; //按键
右下
uint8 k_right_up; //按键 右上
uint8
k_e; //按键
其他，保留
uint8
k_f; //按键
其他，保留
uint8
k_g; //按键
其他，保留
uint8
k_h; //按键 其他，保留
} MRAPP_HANDLE_INFO_T;
typedef
struct
{
int32 code;
//手机配置信息：0：初始化；1：去初始化；2：获取手柄信息；
} MRAPP_HANDLE_CODE_T;

## 相关

Copyright ?2005-20010 SKY-MOBI
