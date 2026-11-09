# mr_platEx(6000) - 查询桌面气泡框是否支持

```c
int32 mr_platEx (int32 code = 6000, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

查询是否支持气泡框接口。

## 参数

| 参数 | 说明 |
|---|---|
| input | 无 |
| input_len | 无 |
| output | int32 指针, 返回1 表示禁止长在线后台显示，返回0表示运行显示 |
| output_len | 无 |
| cb | 无 |

## 返回值

MR_SUCCESS ：支持后台气泡框接口
MR_FAILED ：不支持后台气泡接口
MR_IGNORE
：未实现接口

## 示例

```c
/*mrp code*/
```

## 相关

Copyright ?2005-20010 SKY-MOBI
