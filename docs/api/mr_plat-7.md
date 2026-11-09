# mr_plat(7) - 按键音开启关闭控制

```c
int32 mr_plat(int32 code = 7, int32 param)
```

## 说明

按键音开启关闭控制。

## 参数

| 参数 | 说明 |
|---|---|
| param | 0 关闭， 1 开启 |

## 返回值

MR_SUCCESS ： 成功
MR_FAILED ： 失败
MR_IGNORE ：
不支持该功能

## 备注

Mythroad透明调用这个接口。APP层上的对应命令将会透明调用至移植层，移植层的返回值也将透明返回至APP层。该扩展接口可用于特殊的平台命令/操作。code的说明详见附录A。对于移植层不支持的code，移植层需要返回MR_IGNORE以告知VM和APP。

## 示例

```c
/*mrp code*/
mrc_plat( 7, 1 );
```

## 相关

Copyright ?2005-20010 SKY-MOBI
