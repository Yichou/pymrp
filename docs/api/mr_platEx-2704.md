# mr_platEx(2704) - 获得PCM数据

```c
int32 mr_platEx (int32 code = 2704, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

在录音启动的接口中将格式设置成pcm，src_type设置为SRC_STREAM的情况下，调用本接口来获得pcm数据
。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | pcm数据地址 |
| output_len | pcm数据的长度 |
| cb | 处理完本次pcm数据后需要调用的函数 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 示例

```c
/*mrp code*/
uint8* pdata = NULL;
int32 re, len = 10;
MR_PLAT_EX_CB cb = NULL;
re = mrc_platEx( 2704 , NULL, 0, (uint8**)&amp;pdata, &amp;len, &amp;cb
);
if(MR_SUCCESS == re)
{
cb( (uint8*)pdata, len
);
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
