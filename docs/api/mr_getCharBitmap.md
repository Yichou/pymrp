# mr_getCharBitmap

```c
const char *mr_getCharBitmap(uint16 ch, uint16 fontSize, int *width, int *height)
```

## 说明

获取字符点整。

## 参数

| 参数 | 说明 |
|---|---|
| ch | endian，比如“1”为0x0031若CPU是big endian，则该Unicode码是big endian，比如“1”为0x0031 |
| fontSize | MR_FONT_BIG合并；若支持一种字体，将所有字体合并。 |
| width, height | 返回的字符的宽和高 |

Unicode码，若CPU是little endian，则该Unicode码是little
字体大小，可能的值是
MR_FONT_SMALL,
MR_FONT_MEDIUM,
MR_FONT_BIG如果手机平台不支持多种字体，可以合并一些字体，具体策略是：若支持两种字体，将MR_FONT_MEDIUM、

## 返回值

放回字符的点整的起始地址，如果失败返回NULL.
当字库里没有该字体的点阵信息是，希望不要返回失败，建议返回一个”口”这样的字体信息。

## 备注

获取unicode码ch指向的字体的点阵信息，并告之该字体的宽和高，获取到的点阵信息每一个bit表示字体的一个象素。目前的版本字体每行的象素都是以紧凑的方式排布，即不按字节对齐的方式。
注：若字库中的字体每行的象素必须按字节对齐，也就是说如果一个字体宽为12，则需要用两个字节来表示该信息，第二个字节的后四个bit为0，从第三个字节开始才表示下一行的点阵数据。则需要特别编译特殊的版本。

## 相关

Copyright ?2005-20010 SKY-MOBI
