# mr_platEx(1305) - 获得指定盘符的剩余空间

```c
int32 mr_platEx (int32 code = 1305, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获得指定盘符的剩余空间大小。

## 参数

| 参数 | 说明 |
|---|---|
| input | 盘符标记（不区分大小写ASCII） |
| input_len | 字符串长度 |
| output | T_DSM_FREE_SAPCE结构的指针 |
| output_len | T_DSM_FREE_SAPCE结构长度 |
| cb | 无 |

## 返回值

MR_SUCCESS :获得大小成功
MR_FAILED
:获得失败
MR_IGNORE :不支持该功能
注：要得到以byte 为单位的大小值可以通过
account×unit 得到.

## 备注

Typedef struct
{
uint32 total; //总的大小
uint32
tunit; //总大小的单位
uint32 account; //剩余空间的大小
uint32
unit; //剩余大小的单位
}T_DSM_FREE_SAPCE
Unit：
1
：单位是
byte
1024
：单位是 k byte
1024x1024
：单位是 m byte
1024x1024x1024：单位是 g
byte

## 示例

```c
/*mrp code*/
T_DSM_FREE_SAPCE *getInfo = NULL;
char *disk = NULL;
int32 len =
0;
disk = "A";
mrc_platEx( 1305, (uint8*)disk, sizeof(char),
(uint8**)&amp;getInfo, (int32*)&amp;len, NULL
);
mrc_printf( "Info:totalSpace=%d/%d,
freeSpace=%d/%d",
getInfo-&gt;total, getInfo-&gt;tunit,
getInfo-&gt;account, getInfo-&gt;unit );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
