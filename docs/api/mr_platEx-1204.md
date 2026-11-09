# mr_platEx(1204) - 切换目录

```c
int32 mr_platEx (int32 code = 1204, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

切换目录。

## 参数

| 参数 | 说明 |
|---|---|
| input | 目录字符串指针 |
| input_len | 目录字符串长度 |
| output | 返回的路径字串缓冲。（GB编码）（只在输入为“Y”获取当前的路径设置的时候有效） |
| output_len | 返回的路径字串的长度。 |
| cb | 无 |

## 返回值

MR_SUCCESS ：成功
MR_FAILED ：失败
MR_IGNORE
：不支持该功能

## 备注

功能：将SkyEngine的根目录切换至新目录。目录字符串如：”C:/App/”，第一个字符表示切换至的存储设备：（盘符
不区分大小写，GB编码）
A： 普通用户不可见（不可操作）存储盘
B：
普通用户可操作存储盘（即可usb连接在PC上操作）
C： 外插存储设备，如mmc，sd，t-flash等
D：
第二外插存储设备
Y： 获取当前的路径设置，返回型如：”C:/App/”（即必须符合上述输入标准），gb编码
Z：
返回应用刚启动时候的目录（后继子串参数无意义）
X：
进入vm的根目录（后继子串参数无意义）。这个根目录必须放在用户不可见的，不能卸载的盘上。在这个根目录下可以保存一些设置信息，及收费信息等。
D～W：
保留。
第二、第三字符为“:/”，第四字符起为该存储设备上的目录名。

## 示例

```c
/* mrp code*/
BOOL SwitchDisk(const char* strDisk)
//strDisk为目录字符串,如"A:/","B:/"
{
int
ret=MR_FAILED;
unsigned char*
output=NULL;
int32 output_len=0;
#ifdef WIN32
return
FALSE;
#endif
ret=mrc_platEx(
1204, (uint8*)strDisk, mrc_strlen(strDisk), &amp;output, &amp;output_len, NULL
);
return ret;
}
BOOL GetDir(char* strDir)
{
int32
ret=MR_FAILED;
int32 len;
unsigned
char* pDir=NULL;
#ifdef
WIN32
return
FALSE;
#endif
ret
=mrc_platEx( 1204, (uint8*)"Y", 1, &amp;pDir, &amp;len, NULL
);
mrc_memcpy( (void*)strDir, (void*)pDir, len
);
return ret;
}
```

## 相关

Copyright ?2005-20010 SKY-MOBI
