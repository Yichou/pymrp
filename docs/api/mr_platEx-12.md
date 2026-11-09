# mr_platEx(12) - 获取手机平台的picture存储目录名称

```c
int32 mr_platEx (int32 code = 12, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

获取手机平台的picture存储目录名称。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | 返回指向名称字串的指针（gb编码） |
| output_len | 输出参数大小（字节数） |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 示例

```c
/*mrp code*/
char*pStor = NULL;
int32 len = 0;
mrc_platEx( 12, NULL, 0,
(uint8**)&amp;pStor, (int32*)&amp;len, NULL );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
