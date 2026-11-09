# mr_platEx(1323) - 设置异步转后台

```c
int32 mr_platEx (int32 code = 1323, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

设置异步转后台。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_backstage_async_runinfo_t 结构指针 |
| input_len | mr_backstage_async_runinfo_t 结构大小 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 备注

typedef struct {
uint32
bSilence; //客户端不需要提示是否退出后台应用
uint32 nTimerInterval;
//延时启动的毫秒数
}mr_backstage_async_runinfo_t;

## 示例

```c
/*mrp code*/
```

## 相关

Copyright ?2005-20010 SKY-MOBI
