# mr_platEx(1306) - 获取存储设备的名称

```c
int32 mr_platEx (int32 code = 1306, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

用来获取厂商自己设置的A、B、C、D、等存储设备的名称，例如：B设备名字为“U盘”,如果查询的设备不存在则返回MR_FAILED。（展讯接口）

## 参数

| 参数 | 说明 |
|---|---|
| input | 盘符标记（不区分大小写ASCII） |
| input_len | 字符串长度 |
| output | 设备名称。Unicode编码，以双0结尾。 比如 “U盘” |
| output_len | 设备名称的字节长度（byte），包括结尾符双0的长度； |
| cb | 无 |

## 返回值

MR_SUCCESS :获得大小成功
MR_FAILED
:获得失败
MR_IGNORE :不支持该功能

## 示例

```c
/*mrp code*/
int32 len = 0;
const char* pDisk = "D:/";
char* pName = NULL;
char
name[60] = { 0 };
mrc_platEx( 1306, (uint8*)pDisk, strlen(pDisk),
(uint8**)&amp;pName, (int32*)&amp;len, NULL );
wstr2str( (PCWSTR)pName,
(PSTR)&amp;name[0], sizeof(name) ); //unicode to string.
mrc_printf(
"Dir name: %s", name );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
