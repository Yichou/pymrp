# mr_start_dsm_ex

```c
int32 mr_start_dsm_ex(const char* path, const char* entry)
```

## 说明

通过入口参数来启动虚拟机。

## 参数

| 参数 | 说明 |
|---|---|
| path | mrp文件路径 |
| entry | dsm入口标志，该标志用于启动非dsm根目录的项目。启动dsm根目录时该参数填NULL（相当于运行”*A”固化应用）。若该参数以’*’开头，则执行固化应用（参见“注册固化应用”小节），”*A”表示index为0的应用，”*B”表示index为1的应用，以此类推。若该参数以’%’开头，则执行根目录下的mrp文件，如”%QQ.mrp”执行QQ.mrp文件。 |

## 返回值

成功启动返回MR_SUCCESS,失败返回MR_FAILED.

## 备注

初始化SkyEngine引擎，并运行指定的应用。当SkyEngine引擎启动时会调用mr_mem_get获取引擎需要的内存。
mr_mem_get函数由移植者实现，以取得引擎需要的内存。entry是SkyEngine入口参数。

## 相关

mr_start_dsm
mr_start_dsmB
mr_start_dsmC
Copyright ?2005-20010 SKY-MOBI
