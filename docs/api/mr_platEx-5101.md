# mr_platEx(5101) - 修改本地UI的左右软键文本

```c
int32 mr_platEx (int32 code = 5101, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

修改菜单,TEXT,dialog等本地UI组件的左右软键文本。

## 参数

| 参数 | 说明 |
|---|---|
| input | t_mr_setkeystr 结构 |
| input_len | t_mr_setkeystr 结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构:
typedef struct
{
int keypos;//位置 左键 =
0,右键=1.中间键=2;
char* keystr;//字符串指针
}t_mr_setkeystr;

## 相关

Copyright ?2005-20010 SKY-MOBI
