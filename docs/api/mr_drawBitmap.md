# mr_drawBitmap

```c
void mr_drawBitmap(uint16* bmp, int16 x, int16 y, uint16 w, uint16 h)
```

## 说明

绘制BITMAP。

## 参数

| 参数 | 说明 |
|---|---|
| bmp | 图片在内存中存放的地址首指针 |
| x,y | 图片左上角在屏幕中的坐标 |
| w,h | 图片高 |

图片宽,

## 返回值

无返回值。

## 备注

将bmp指向的Bitmap图片绘制于屏幕中。bmp指向的图片格式是16bit色深的w*h大小的Bitmap图片，象素顺序是：从左上角的象素开始，从左到右，从上到下排列象素。每个象素的16bit的r,g,b分别为：5
bit、6 bit、5
bit。
如纯红色为：0b1111100000000000
如纯绿色为：0b0000011111100000
如纯篮色为：0b0000000000011111

## 相关

Copyright ?2005-20010 SKY-MOBI
