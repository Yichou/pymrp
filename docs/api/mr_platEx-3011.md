# mr_platEx(3011) - 显示gif动画

```c
int32 mr_platEx (int32 code = 3011, uint8* input, int32 input_len, uint8** output, int32* output_len, MR_PLAT_EX_CB* cb )
```

## 说明

显示gif动画的接口（直接绘制到frame
buffer上），每一帧动画的显示也都是mtk来控制。动画停止需要调用mr_plat(3012,句柄)。

## 参数

| 参数 | 说明 |
|---|---|
| input | T_DRAW_DIRECT_REQ数据结构指针 |
| input_len | T_DRAW_DIRECT_REQ数据结构大小 |
| output | T_DSM_COMMON_RSP数据结构指针 |
| output_len | T_DSM_COMMON_RSP数据结构大小 |
| cb | 无 |

## 返回值

MR_SUCCESS
成功
MR_FAILED
失败
MR_IGNORE 不支持该功能

## 备注

输入数据结构：
typedef struct
{
char
*src; //当type为SRC_STREAM时，此参数为图片数据流buffer；当type为SRC_NAME时，此参数为图片相对路径
int32
src_len;
//当type为SRC_STREAM时，此参数为图片数据流buffer大小；当type为SRC_NAME时，此参数为0
int32
src_type;
//枚举MRAPP_SRC_TYPE
int32
ox; //图片显示在x坐标
int32
oy;
//图片显示在y坐标
int32
w;
//图片宽度
int32
h;
//图片高度
}T_DRAW_DIRECT_REQ;
typedef enum
{
SRC_NAME = 0,
//传到移植接口的是文件名
SRC_STREAM
//传到移植接口的是图片数据流
}MRAPP_SRC_TYPE;
输出数据结构：
typedef struct
{
int32
p1;
//gif动画句柄
}T_DSM_COMMON_RSP;

## 示例

```c
/*mrp code*/
#define GIF_ANIMATION "OATfile\\pic_test\\shoes.gif"
T_DRAW_DIRECT_REQ
drawReq = { 0 };
T_DSM_COMMON_RSP *drawRes = NULL;
int32
leninfo;
drawReq.h = 40;
drawReq.w = 40;
drawReq.ox =
10;
drawReq.oy = 10;
drawReq.src =(char
*)GIF_ANIMATION;
drawReq.src_type = SRC_NAME ;
mrc_platEx( 3011, (uint8*)&amp;drawReq, sizeof( T_DRAW_DIRECT_REQ),
(uint8**)&amp;drawRes, &amp;leninfo, NULL );
mrc_refreshScreen( (int16)10,
(int16)10, (uint16)40, (uint16)40 );
```

## 相关

mr_plat(3012)
Copyright ?2005-20010 SKY-MOBI
