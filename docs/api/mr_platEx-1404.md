# mr_platEx(1404) - 调用平台本地浏览界面

```c
int32 mr_platEx (int32 code = 1404, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

创建浏览，调用平台本地浏览界面。

## 参数

| 参数 | 说明 |
|---|---|
| input | 指向MR_T_FMGR_REQ结构的指针 |
| input_len | MR_T_FMGR_REQ结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

数据结构：
typedef struct
{
int32 dft_list;
char
list_path[260];
//gb绝对路径
}MR_T_FMGR_REQ;
Dft_list:
0：MR_DSPL_NONE
1：MR_DSPL_IMAGE
2：MR_DSPL_AUDIO
3：MR_DSPL_VIDEO
4：MR_DSPL_NES
注：当dft_list
等于MR_DSPL_NONE的时候才以list_path中路径为准，
其他的都调用手机默认的路径,选中还是返回的操作由MR_LOCALUI_EVENT（10）
事件传递给VM
0：MR_LOCALUI_OK
（表示用户选择了一个文件）
1：MR_LOCALUI_CANCEL（表示用户选择退出浏览这个功能）

## 相关

Copyright ?2005-20010 SKY-MOBI
