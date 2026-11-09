# mr_platEx(6004) - 查询最后一次联网时间

```c
int32 mr_platEx (int32 code = 6004, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

查询当前SIM卡的最后一次联网时间。

## 参数

| 参数 | 说明 |
|---|---|
| input | mr_datetime结构的指针 |
| input_len | mr_datetime结构的长度 |
| output | 无 |
| output_len | 无 |
| cb | 无 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED，未实现返回MR_IGNORE.

## 示例

```c
/*mrp code*/
```

## 相关

Copyright ?2005-20010 SKY-MOBI
