# mr_platEx(1004) - 切换到后台运行

```c
int32 mr_platEx (int32 code = 1004, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

后台运行。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_backstage_st 结构的指针 |
| input_len | mr_backstage_st 结构的长度 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

通知移植层本应用需要后台运行
数据结构：
typedef struct
{
int32 appid;
//app id
uint8 describe[20]; //应用标志符 -
"ipqq"
uint8* param;
//预留扩展用
}mr_backstage_st;

## 示例

```c
/*mrp code*/
int32 MINApp(int32 appid)
{
mr_backstage_st backRunIn;
int32
ret;
memset(&amp;backRunIn,0,sizeof(mr_backstage_st));
backRunIn.appid =
appid;//当前移植层只做了appid的判断，用于区分是QQ还是其他产品，从而根据appid显示不同的icon；
ret = mrc_platEx(1004, (uint8*)&amp;backRunIn, sizeof(mr_backstage_st), 0, 0,
0);
return ret;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
