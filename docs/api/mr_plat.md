# mr_plat

```c
int32 mr_plat(int32 code, int32 param)
```

## 说明

基本的平台调用接口，对应于应用层的mrc_plat接口。

## 参数

| 参数 | 说明 |
|---|---|
| code | 扩展接口事件 |
| param | 事件参数 |

## 返回值

返回对应code事件的处理结果，MR_SUCCESS表示成功，MR_FAILED表示失败，MR_IGNORE表示对应的code.在老的接口上，有些code的返回值会加上MR_PLAT_VALUE_BASE
= 1000，具体请参考每个code的详细定义。

## 备注

Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。code的说明详见附录A。对于移植层不支持的code，移植层需要返回MR_IGNORE以告知VM和APP。

## 相关

Copyright ?2005-20010 SKY-MOBI
