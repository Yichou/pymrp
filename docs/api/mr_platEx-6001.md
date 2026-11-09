# mr_platEx(6001) - 显示桌面气泡框

```c
int32 mr_platEx (int32 code = 6001, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

显示气泡框。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_backstage_tipinfo_t 结构指针 |
| input_len | mr_backstage_tipinfo_t 结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS ：成功
MR_FAILED ：失败
MR_IGNORE ：未实现

## 备注

typedef struct{
uint32 style;
/*这里可以是浮动的，也可以是模态的*/
uint8* icon_path; /*icon 文件名*/
int16
icon_width, icon_height; /*图片宽高*/
uint8* title;
/*对话框标题*/
uint8* content; /*对话框内容*/
uint8* lsk; //left sofkt
key
uint8* rsk; //right soft
key
}mr_backstage_tipinfo_t;

## 示例

```c
/*mrp code*/
```

## 相关

Copyright ?2005-20010 SKY-MOBI
