#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <strings.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <wiringPi.h>
#include "data.h"
#include "git_data.h"
#include "utf_8_to_gb3212.h"
#include <pthread.h>
#include <time.h>
#include <stdarg.h>
#include <sys/timeb.h>
#include <sys/time.h>

#include "mSysLog.h"

#define uchar unsigned char
#define uint unsigned int
#define ulong unsigned long

#define Block_log_information   0
#define Get_log_information     1
uint log_status = 1;

// 位置配置
#define Interface_Spin_0			0
#define Interface_Spin_90			1
#define Interface_Spin_180			2
#define Interface_Spin_270			3
#define Interface_Spin  Interface_Spin_180

// 屏参
#define Interface_Row			8
#define Interface_Column		128	
#define Interface_Row_unit		8
#define Interface_Column_unit	1

#define Min(x, y)			x > y ? y : x
#define Max(x, y)			x < y ? y : x

// 封装接口
#define LCD_mode_AT						0
#define LCD_mode_table_5x8				1
#define LCD_mode_table_8x16				2
#define LCD_mode_table_16x16			3
#define LCD_mode_table_image			4
#define LCD_mode_table_Make_words		5
#define LCD_Command_header	            "0 0 0 0,0"

#define printf_Row(Row)	        printf("printf_Row(%d)\n",Row);

#define Start_Receive_data_buffer		0
#define Continue_Receive_data_buffer	1

#define original_ASCII_data	6
#define now_ASCII_data		6

#define original_Chinese_data	(original_ASCII_data+original_ASCII_data)
#define now_Chinese_data		(now_Chinese_data+now_Chinese_data)

#define coding_get_ratio_results(original, now, data)		(data % original * now/original)
#define coding_get_8_ASCII(i)		coding_get_ratio_results(5, 5, i)
#define coding_get_16_ASCII(i)		coding_get_ratio_results(original_ASCII_data, now_ASCII_data, i)
#define coding_get_16_Chinese(i)	coding_get_ratio_results(original_Chinese_data, (now_ASCII_data + now_ASCII_data), i)

int rs = 9;
int reset = 7;
int cs = 8;
int sda = 10;
int clk = 11;
//写指令到 LCD 模块 
void transfer_command(int data1) 
{ 
  char i; 
  digitalWrite(cs, 0); 
  digitalWrite(rs, 0); 
  for(i=0;i<8;i++) 
  { 
    digitalWrite(clk, 0); 
    if(data1&0x80)
      digitalWrite(sda, 1); 
    else 
      digitalWrite(sda, 0); 
    digitalWrite(clk, 1); 
    data1<<=1; 
  } 
  digitalWrite(cs, 1); 
} 
//写数据到 LCD 模块 
void transfer_data(int data1) 
{ 
  char i; 
  digitalWrite(cs, 0); 
  digitalWrite(rs, 1); 
  for(i=0;i<8;i++) 
  { 
    digitalWrite(clk, 0); 
    if(data1&0x80)
      digitalWrite(sda, 1); 
    else 
      digitalWrite(sda, 0); 
    digitalWrite(clk, 1); 
    data1<<=1; 
  } 
  digitalWrite(cs, 1); 
} 
// 写地址
void lcd_address(uchar page,uchar column) 
{ 
  column=column-1; //我们平常所说的第 1 列，在 LCD 驱动 IC 里是第 0 列，所以在这里减去 1。 
  page=page-1; //我们平常所说的第 1 页，在 LCD 驱动 IC 里是第 0 页，所以在这里减去 1。 
  transfer_command(0xb0+page); //设置页地址。每页是 8 行。一个画面的 64 行被分成 8 个页。 
  transfer_command(((column>>4)&0x0f)+0x10); //设置列地址的高 4 位 
  transfer_command(column&0x0f); //设置列地址的低 4 位 
} 
//LCD模块初始化
void initial_lcd() {
  wiringPiSetupGpio();
  pinMode(rs, OUTPUT);
  pinMode(reset, OUTPUT);
  pinMode(cs, OUTPUT);
  pinMode(sda, OUTPUT);
  pinMode(clk, OUTPUT);
  digitalWrite(reset, 0);  //低电平复位 
  usleep(800000);
  digitalWrite(reset, 1);  //复位完毕 
  usleep(800000);
  transfer_command(0xe2);  //软复位
  usleep(500000);
  transfer_command(0x2f);  //打开内部升压
  usleep(500000);
  transfer_command(0x81);  //微调对比度
  transfer_command(0x39);  //微调对比度的值，可设置范围0x00～0xFF(原值0X33）
  transfer_command(0xeb);  //1/9偏压比（bias）
  transfer_command(0xc6);  //行列扫描顺序：从上到下、从左到右
  transfer_command(0xaf);  //开显示
  transfer_command(0xc3);  //纵向显示：从上到下、从左到右 FPC在右边
}

uchar DATA_8_Bit_swap(uchar source) {
  uchar swap_data = source;
  swap_data = ((swap_data & 0xF0) >> 4) | ((swap_data & 0x0F) << 4);
  swap_data = ((swap_data & 0xCC) >> 2) | ((swap_data & 0x33) << 2);
  swap_data = ((swap_data & 0xAA) >> 1) | ((swap_data & 0x55) << 1);
  return swap_data;
}

// 像素点
#if (Interface_Spin == Interface_Spin_0)
struct Interface_Pixel_unit{
  uchar Pixel_0:1;
  uchar Pixel_1:1;
  uchar Pixel_2:1;
  uchar Pixel_3:1;
  uchar Pixel_4:1;
  uchar Pixel_5:1;
  uchar Pixel_6:1;
  uchar Pixel_7:1;
};
#elif (Interface_Spin == Interface_Spin_180)
struct Interface_Pixel_unit{
  uchar Pixel_7:1;
  uchar Pixel_6:1;
  uchar Pixel_5:1;
  uchar Pixel_4:1;
  uchar Pixel_3:1;
  uchar Pixel_2:1;
  uchar Pixel_1:1;
  uchar Pixel_0:1;
};	
#endif	

// 屏幕的实际像素阵列
struct Interface_Pixel_overall {
  struct Interface_Pixel_unit Pixel_unit[Interface_Row][Interface_Column * Interface_Column_unit];
  struct Interface_Pixel_unit Pixel_unit_buf[Interface_Row][Interface_Column * Interface_Column_unit];
  //uchar Pixel_unit[Interface_Row][Interface_Column * Interface_Column_unit];
  //uchar Pixel_unit_buf[Interface_Row][Interface_Column * Interface_Column_unit];
};

void interface_Pixel_unit(struct Interface_Pixel_overall *Interface, int status){
  //MSYSLOG("MT", "sizeof(Interface->Pixel_unit) = %d", sizeof(Interface->Pixel_unit));
  if(status)
    memset(&Interface->Pixel_unit, 0xff, sizeof(Interface->Pixel_unit)); 
  else 
    memset(&Interface->Pixel_unit, 0x00, sizeof(Interface->Pixel_unit));  
}

void interface_Pixel_unit_buf(struct Interface_Pixel_overall *Interface, int status) {
  if(status)
    memset(&Interface->Pixel_unit_buf, 0xff, sizeof(Interface->Pixel_unit_buf));
  else
    memset(&Interface->Pixel_unit_buf, 0x00, sizeof(Interface->Pixel_unit_buf));
}

// 像素描点
void set_interface_Pixel_unit(struct Interface_Pixel_overall *Interface, int Pixel_x, int Pixel_y, int status) {
  if( (Pixel_x >= 0) & (Pixel_x < 64) & (Pixel_y >= 0) & (Pixel_y < Interface_Column * Interface_Column_unit)){
    //Interface->Pixel_unit[Pixel_x/Interface_Row_unit][Pixel_y][Pixel_x%Interface_Row_unit].Pixel = status;
    switch (Pixel_x % Interface_Row_unit) {
      case 0: 
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_0 = status;
        break;
      case 1:
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_1 = status;
        break;
      case 2: 
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_2 = status;
        break;
      case 3: 
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_3 = status;
        break;
      case 4: 
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_4 = status;
        break;
      case 5:
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_5 = status;
        break;
      case 6:
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_6 = status;
        break;
      case 7:
        Interface->Pixel_unit[Pixel_x / Interface_Row_unit][Pixel_y].Pixel_7 = status;
        break;
      default: 
        break;
    }
  }
}
// 全部像素点显示相同
void set_all_interface(struct Interface_Pixel_overall *Interface, int status) {
  if(status) {
    interface_Pixel_unit(Interface, 1);
    interface_Pixel_unit_buf(Interface, 0);
  }
  else {
    interface_Pixel_unit(Interface, 0);
    interface_Pixel_unit_buf(Interface, 1);
  }
}

// 像素点描线
void set_interface_Line_drawing(struct Interface_Pixel_overall *Interface, int Start_x, int Start_y, int End_x, int End_y, int status){
  int i,j;
  int start_x,start_y,end_x,end_y;
  start_x = Min(Start_x,End_x);
  start_y = Min(Start_y,End_y);

  end_x = Max(Start_x,End_x);
  end_y = Max(Start_y,End_y);

  for(int i=start_x;i<end_x;i++){
    for(int j=start_y;j<end_y;j++){
#if (Interface_Spin == Interface_Spin_0)
      set_interface_Pixel_unit(Interface, i, j, status);
#elif (Interface_Spin == Interface_Spin_180)
      set_interface_Pixel_unit(Interface, ((Interface_Row - (i/Interface_Row_unit) - 1) * Interface_Row_unit + i % Interface_Row_unit), (Interface_Column * Interface_Column_unit - 1 - j), status);
#endif
    }
  }
}

// 	test 打印测试
void pri_terminal_Pixel_overall(int addr_value,int Interface_x,int Interface_y){
  int i,j;
  struct Interface_Pixel_overall *Interface = (struct Interface_Pixel_overall *)addr_value;
  for(i=0;i<Interface_x;i++){
    for(j=0;j<Interface_y;j++){
      //printf("%d ",Interface->Pixel_unit[i/Interface_Row_unit][j][i%Interface_Row_unit].Pixel);
      switch (7 - ((Interface_x - i - 1)%Interface_Row_unit)) {
        case 0:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_0);}break;
        case 1:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_1);}break;
        case 2:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_2);}break;
        case 3:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_3);}break;
        case 4:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_4);}break;
        case 5:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_5);}break;
        case 6:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_6);}break;
        case 7:{printf("%d ",Interface->Pixel_unit[(Interface_x - i - 1)/Interface_Row_unit][(Interface_y - j - 1)].Pixel_7);}break;
        default:{;}break;
      }
    }printf("\n");
  }
}

// 数据 buf 数据
uchar git_Pixel_overall_data(struct Interface_Pixel_overall *Interface, int Page, int position) {
  uchar value = 0;
  switch (Interface_Spin) {
    case Interface_Spin_0:
      value = *(char*)&Interface->Pixel_unit[Page][position];
      break;
    case Interface_Spin_90:
      break;
    case Interface_Spin_180:
      value = *(char*)&Interface->Pixel_unit[Page][position];
      break;
    case Interface_Spin_270:
      break;
    default:
      break;
  }
  return value;
}

uchar git_Pixel_overall_data_buf(struct Interface_Pixel_overall *Interface, int Page, int position) {
  uchar value = 0;
  switch (Interface_Spin) {
    case Interface_Spin_0: 
      value = *(char*)&Interface->Pixel_unit_buf[Page][position];
      break;
    case Interface_Spin_90:
      break;
    case Interface_Spin_180:
      value = *(char*)&Interface->Pixel_unit_buf[Page][position];
      break;
    case Interface_Spin_270:
      break;
    default:
      break;
  }
  return value;
}
// 128x64 interface_refresh
void lcd_interface_refresh(struct Interface_Pixel_overall *Interface) {
  uchar i, j;
  for(i = 0; i < 8; i++) {
    for(j = 0; j < Interface_Column * Interface_Column_unit; j++) {
      if( git_Pixel_overall_data(Interface, i, j) != git_Pixel_overall_data_buf(Interface, i, j) ) {
        lcd_address(1 + i, j + 1);
        transfer_data(git_Pixel_overall_data(Interface, i, j));
      }
      *(char*)&Interface->Pixel_unit_buf[i][j] = *(char*)&Interface->Pixel_unit[i][j];
    }
  }
}

// 左右留边
void set_interface_Pixel_uchar_8bit(struct Interface_Pixel_overall *Interface, int Page, int position, uchar value){
  if((0<=Page)&(Page<Interface_Row)&(0<=position)&(position<(Interface_Column - 2))){			// 左右边
#if (Interface_Spin == Interface_Spin_0)
    *((char *)&(((struct Interface_Pixel_overall *)Interface)->Pixel_unit[Page][position + 1])) = value;
#elif (Interface_Spin == Interface_Spin_180)
    *((char *)&(((struct Interface_Pixel_overall *)Interface)->Pixel_unit[Interface_Row -1 - Page][Interface_Column*Interface_Column_unit - 1 - (position + 1)])) = DATA_8_Bit_swap(value);
#endif
  }
}

// 写字符
void set_interface_Pixel_unit_8bit_5x8(struct Interface_Pixel_overall *Interface, int Page, int position, uchar value){
  for(int i = 0; i < 5; i++){
    set_interface_Pixel_uchar_8bit(Interface, Page, (position * 6 + i), ascii_table_5x8[value - 0x20][i]);
  }
}
//写入 字符串
int lcd_add_interface_loading_5x8(struct Interface_Pixel_overall *Interface, int Page, int position, char*dp){
  int i, j;
  int count = 0;
  while(*(dp + count)) {
    set_interface_Pixel_unit_8bit_5x8(Interface, Page, (position + count),*(dp + count));
    count++;
  }
}


// 写字符
void set_interface_Pixel_unit_8bit_8x16(struct Interface_Pixel_overall *Interface, int Page, int position, uchar value){
  int pat;
  for(int i = 0; i < 12; i++) {
    set_interface_Pixel_uchar_8bit(Interface, Page + (i / original_ASCII_data), (position * now_ASCII_data + coding_get_16_ASCII(i)), ascii_table_6x12[value - 0x20][i]);
  }
}

// 写中文
void set_interface_Pixel_unit_8bit_16x16(struct Interface_Pixel_overall *Interface, int Page, int position, unsigned int value){
  int pat;
  for(int i = 0; i < 12; i++){
    set_interface_Pixel_uchar_8bit(Interface, Page, (position * now_ASCII_data + coding_get_16_Chinese(i)), GB2312_13_data_code[value][i]);
  }
  for(int i = 0; i < 12; i++){
    set_interface_Pixel_uchar_8bit(Interface, Page + 1, (position * now_ASCII_data + coding_get_16_Chinese(i)), GB2312_13_data_code[value][i + 12]);
  }
}

// 写字串
int lcd_add_interface_loading_8x16(struct Interface_Pixel_overall *Interface, int Page, int position, char*dp){
  int i, j;
  int count = 0;
  while( *(dp + count) ) {
    set_interface_Pixel_unit_8bit_8x16(Interface, Page, (position + count),*(dp + count));
    count++;
  }
}

struct code_convert_data{
  int value;
  int count;
  unsigned char code_convert_buf[1024];
};
void com_code_convert_data(int code_convert_addr){
  struct code_convert_data *code_convert  = (struct code_convert_data *)code_convert_addr;
  bzero(&code_convert->code_convert_buf, sizeof(code_convert->code_convert_buf));
  code_convert->value = 0;
  code_convert->count = 0;
}

void git_GB3212_break_down_value(int code_convert_addr){
  struct code_convert_data *code_convert  = (struct code_convert_data *)code_convert_addr;
  // 数据计算
  if(0 == code_convert->code_convert_buf[code_convert->count] ){
    code_convert->value = 0;
    code_convert->count = 0;
  } else if ((code_convert->code_convert_buf[code_convert->count] >= 32)&(code_convert->code_convert_buf[code_convert->count] < Interface_Column*Interface_Column_unit)) {
    code_convert->value = code_convert->code_convert_buf[code_convert->count];
  } else if (code_convert->code_convert_buf[code_convert->count] > Interface_Column*Interface_Column_unit) {
    code_convert->value = code_convert->code_convert_buf[code_convert->count] * 256 + code_convert->code_convert_buf[code_convert->count+1];
  }
}
// 写字串
int lcd_add_interface_loading_16x16(struct Interface_Pixel_overall *Interface, int Page, int position, char*dp){
  struct code_convert_data code_convert;        // 转数据
  com_code_convert_data((int)&code_convert);    // 字符转换
  // utf8 to GB3212
  UTF8_to_GB3212(dp,strlen(dp),code_convert.code_convert_buf,sizeof(code_convert.code_convert_buf));
  // 数据写入
  do{
    git_GB3212_break_down_value( (int)&code_convert );
    if(code_convert.value == 0);
    else {
      if( (0x20 <= code_convert.value) & (code_convert.value < Interface_Column*Interface_Column_unit) ) {
        //set_interface_Pixel_unit_8bit_5x12(Interface,Page+1,(position+(code_convert.count)),code_convert.value);
        set_interface_Pixel_unit_8bit_8x16(Interface, Page, ( position + (code_convert.count) ), code_convert.value);
        code_convert.count = code_convert.count + 1;
      }
      else if( (0xA1A1 <= code_convert.value)&(code_convert.value <= 0xF7FE) ) {
        set_interface_Pixel_unit_8bit_16x16(Interface, Page, (position + (code_convert.count)), ( (code_convert.value - 0xA1A1) / 256 * 94 + ( (code_convert.value - 0xA1A1) % 256) ) );
        code_convert.count = code_convert.count  + 2;
      }
    }
  }while(code_convert.value );
}

void init_interface(struct Interface_Pixel_overall *Interface) {
  set_all_interface(Interface, 0);  // clean screen
  lcd_interface_refresh(Interface);
}

struct lcd_add_interface_buf_data{
  uchar* source;                    // dp 使用
  uchar* bufs;
  int Statistical_line_breaks;      // 统计换行
  uchar buf[128];
};
// 初始化
void init_lcd_add_interface_buf_data(int addr_value,uchar *dp){
  struct lcd_add_interface_buf_data *buf_data = (struct lcd_add_interface_buf_data *)addr_value;
  buf_data->source = dp;
  buf_data->bufs = (uchar *)&(buf_data->buf);
  buf_data->Statistical_line_breaks = 0;
  memset((void *)&(buf_data->buf),0,sizeof(buf_data->buf));
}
// cp
void add_lcd_add_interface_buf_copy(int addr_value){
  struct lcd_add_interface_buf_data *buf_data = (struct lcd_add_interface_buf_data *)addr_value;
  while(('\0' != *buf_data->source)&('\n' != *buf_data->source)){
    *buf_data->bufs++ = *buf_data->source++;
  }
  buf_data->bufs = (uchar *)&(buf_data->buf);
  if('\n' == *buf_data->source)buf_data->source++;
}
void add_lcd_add_interface_buf(struct Interface_Pixel_overall *Interface, int Page, int position, int mode, uchar *dp, char k){
  struct lcd_add_interface_buf_data buf_data;
  int addr_data = (int)&buf_data;
  // 数据初始化
  init_lcd_add_interface_buf_data(addr_data, dp);
  while('\0' != *buf_data.source){
    add_lcd_add_interface_buf_copy(addr_data);
    //set_interface_Line_drawing(Interface, (Page + buf_data.Statistical_line_breaks * k) * 8, 0, (Page + k * (1 + buf_data.Statistical_line_breaks)) * 8, 128, 0);
    if(LCD_mode_table_5x8 == mode)
      lcd_add_interface_loading_5x8(Interface, (Page + buf_data.Statistical_line_breaks * k), position, buf_data.bufs);
    else if(LCD_mode_table_8x16 == mode)
      lcd_add_interface_loading_8x16(Interface, (Page + buf_data.Statistical_line_breaks * k), position, buf_data.bufs);
    else if(LCD_mode_table_16x16 == mode)
      lcd_add_interface_loading_16x16(Interface, (Page + buf_data.Statistical_line_breaks * k), position, buf_data.bufs);
    buf_data.Statistical_line_breaks = buf_data.Statistical_line_breaks + 1;
    memset((void *)&(buf_data.buf), 0, sizeof(buf_data.buf));
  }
}

// 指令模式
void lcd_add_interface_LCD_mode_AT(struct Interface_Pixel_overall *Interface, int Page, int position, int mode,uchar *dp){
  ;
}
// 小字母模式
void lcd_add_interface_LCD_mode_table_5x8(struct Interface_Pixel_overall *Interface, int Page, int position, int mode, uchar *dp){
  add_lcd_add_interface_buf(Interface, Page, position, mode, dp, 1);
}
// 大英
void lcd_add_interface_LCD_mode_table_8x16(struct Interface_Pixel_overall *Interface, int Page, int position, int mode, uchar *dp){
  add_lcd_add_interface_buf(Interface, Page, position, mode, dp, 2);
}
// 中文
void lcd_add_interface_LCD_mode_table_16x16(struct Interface_Pixel_overall *Interface, int Page, int position, int mode, uchar *dp){
  add_lcd_add_interface_buf(Interface, Page, position, mode, dp, 2);
}

#define LCD_mode_table_Make_words_Signal_strength 		0

// 信号强度
void LCD_mode_table_Make_words_Sub_mode_Signal_strength(struct Interface_Pixel_overall *Interface, int Page, int position, int dp){
  char buf[128];
  int p = dp;
  int x = Page*8;
  int y = position*6;
  int strength;
  p = p + Instruction_parsing_Split(p, (int)buf, ',');
  strength =  atoi(buf);
  memset((void *)buf, 0, sizeof(buf));
  set_interface_Line_drawing(Interface, x, y, x+8, y+12, 0);						// 清屏
  if(strength > 0)
    set_interface_Line_drawing(Interface, x+6, y+1, x+7, y+2, 1);
  if(strength > 1)
    set_interface_Line_drawing(Interface, x+5, y+3, x+7, y+4, 1);
  if(strength > 2)
    set_interface_Line_drawing(Interface, x+4, y+5, x+7, y+6, 1);
  if(strength > 3)
    set_interface_Line_drawing(Interface, x+3, y+7, x+7, y+8, 1);
  if(strength > 4)
    set_interface_Line_drawing(Interface, x+2, y+9, x+7, y+10, 1);
  if(strength > 5)
    set_interface_Line_drawing(Interface, x+1, y+11, x+7, y+12, 1);
}

// 造字模式 (x y mode Sub_mode buf)
void add_interface_LCD_mode_table_Make_words(struct Interface_Pixel_overall *Interface, int Page, int position, int Sub_mode, int dp){
  switch(Sub_mode) {
    case LCD_mode_table_Make_words_Signal_strength:
      LCD_mode_table_Make_words_Sub_mode_Signal_strength(Interface, Page, position, dp);
      break;
  }
}
void lcd_add_interface_LCD_mode_table_Make_words(struct Interface_Pixel_overall *Interface, int Page, int position, uchar *dp){
  char buf[128];
  int p = (int)dp;
  int Sub_mode, strength;
  p = p + Instruction_parsing_Split(p, (int)buf, ',');
  Sub_mode = atoi(buf);
  memset((void *)buf, 0, sizeof(buf));
  add_interface_LCD_mode_table_Make_words(Interface, Page, position, Sub_mode, p);
}

void lcd_add_interface(struct Interface_Pixel_overall *Interface, int Page, int position, int mode, uchar *dp) {
  switch (mode) {
    char buf[128];
    int p = (int)dp;
    int xe, ye, z;
    // 命令模式
    case LCD_mode_AT:
      lcd_add_interface_LCD_mode_AT(Interface, Page, position,mode,dp);
      break;
    // 字符为 5x8
    case LCD_mode_table_5x8:
      lcd_add_interface_LCD_mode_table_5x8(Interface, Page, position,mode,dp);
      break;
    // 字符为 8x16
    case LCD_mode_table_8x16:
      lcd_add_interface_LCD_mode_table_8x16(Interface, Page, position,mode,dp);
      break;
    // 中文
    case LCD_mode_table_16x16:
      lcd_add_interface_LCD_mode_table_16x16(Interface, Page, position,mode,dp);
      break;
    // 点图模式
    case LCD_mode_table_image:
      p = p + Instruction_parsing_Split(p, (int)buf, ',');
      xe = atoi(buf);
      memset((void *)buf, 0, sizeof(buf));
      p = p + Instruction_parsing_Split(p, (int)buf, ',');
      ye = atoi(buf);
      memset((void *)buf,0,sizeof(buf));
      p = p + Instruction_parsing_Split(p, (int)buf, ',');
      z = atoi(buf);
      memset((void *)buf,0,sizeof(buf));
      set_interface_Line_drawing(Interface, Page, position, xe, ye, z);
      break;
    // x y mode Sub_mode buf
    case LCD_mode_table_Make_words:
      lcd_add_interface_LCD_mode_table_Make_words(Interface, Page, position, dp);
      break;
  }
}
struct lcd_interface_refresh_time{
  struct timespec source;
  struct timespec Back;
  char Refresh_Sign;
};
struct lcd_interface_refresh_time Time;

void set_lcd_interface_refresh_time_Refresh_Sign(void) {
  Time.Refresh_Sign = 1;
}

// 接受数据缓存器
struct Receive_data_buffer {
  struct Receive_data_buffer *next;		// 下一个
  struct Receive_data_buffer *previous;	// 上一个
  unsigned int index;					// 编号
  unsigned int length;					// 数据长度
  char *Data_string;			        // 数据存储位置指针
};
struct Receive_data_buffer *head = NULL;

// 数据cp
int Filter_user_strcpy(unsigned char *aims, unsigned char *source, int source_len){
  int count = 0;
  while(source_len - count){
    *(aims + count) = *(source + count);
    count++;
  }
}

void Filter_print_Receive_data_buffer(struct Receive_data_buffer **addr) {
  MSYSLOG("DEBUG", "******************************************");
  MSYSLOG("DEBUG", "(addr) = %d", addr);
  MSYSLOG("DEBUG", "(*addr) = %d", *addr);
  MSYSLOG("DEBUG", "(*addr)->next = %d", (*addr)->next);
  MSYSLOG("DEBUG", "(*addr)->previous = %d", (*addr)->previous);
  MSYSLOG("DEBUG", "(*addr)->index = %d", (*addr)->index);
  MSYSLOG("DEBUG", "(*addr)->length = %d", (*addr)->length);
  MSYSLOG("DEBUG", "(*addr)->Data_strings = %s", (*addr)->Data_string);
  fflush(stdout);
}

int Filter_change_Receive_data_buffer(struct Receive_data_buffer **addr, unsigned char *dat, unsigned int dat_leng, int N_Receive_data_buffer) {
  struct Receive_data_buffer *node = *addr, *node_tmp = NULL;

  // delete behind the addr node
  do {
    node = *addr;
    if( NULL != node ) {
      // find the last one
      while( NULL != node->next )
        node = node->next;
      node_tmp = node->previous;
      free(node_tmp->next->Data_string);
      node_tmp->next->Data_string = NULL;
      free(node_tmp->next);
      node_tmp->next = NULL;
    }
  } while( *addr != node );

  // append one
  (*addr) = (struct Receive_data_buffer *)calloc(1, sizeof(struct Receive_data_buffer));
  if(N_Receive_data_buffer == Start_Receive_data_buffer)
    head = *addr;
  (*addr)->next = NULL;
  if(0 == N_Receive_data_buffer)
    (*addr)->previous = NULL;
  else
    (*addr)->previous = (struct Receive_data_buffer *)addr;
  if(NULL == (*addr)->previous)
    (*addr)->index = 0;
  else
    (*addr)->index = (*addr)->previous->index + 1;
  (*addr)->length = dat_leng;
  (*addr)->Data_string = calloc(1, (dat_leng + 1));
  Filter_user_strcpy((*addr)->Data_string, dat, (*addr)->length);

  if(log_status == Get_log_information)
    Filter_print_Receive_data_buffer(addr);
}

// 承接过滤结果输出
void Filter_refresh_Receive_data_buffer(struct Interface_Pixel_overall *Interface, struct Instruction *parsing, char *server_char_addr) {
  Instruction_parsing_char(server_char_addr, parsing, ' ');
  lcd_add_interface(Interface, parsing->x, parsing->y, parsing->mode, parsing->buf);
  set_lcd_interface_refresh_time_Refresh_Sign();
  // lcd_interface_refresh(Interface_addr);
}
void Filter_header_Receive_data_buffer(struct Interface_Pixel_overall *Interface, struct Instruction *parsing, struct UTP_socket_server *server) {
  static struct Receive_data_buffer *Follow_pointer;
  static struct Receive_data_buffer *Interface_pointer;
  static char Update_interface_Sign;
  static char Update_Sign;
  static char Pointer_initialization_flag;

  if(0 == Pointer_initialization_flag) {
    Follow_pointer = head;
    Interface_pointer = head;
    Pointer_initialization_flag = 1;
  }
  // 头
  if( !strncmp(LCD_Command_header, server->recvline, server->ret) ) {
    MSYSLOG("MT", "Enter !strncmp(LCD_Command_header, server->recvline, server->ret)");
    if(NULL == head) {
      MSYSLOG("MT", "Enter NULL == head.");
      Filter_change_Receive_data_buffer(&head, LCD_Command_header, strlen(LCD_Command_header), Start_Receive_data_buffer);
    }
    else if( !strncmp(head->Data_string, LCD_Command_header, server->ret) ) {
      MSYSLOG("MT", "Enter !strncmp(head->Data_string, LCD_Command_header, server->ret)");
      Update_interface_Sign = 0;
      Update_Sign = 0;
    }
    // 数据头有变动
    else {
      MSYSLOG("MT", "Enter it's not NULL == head and !strncmp(head->Data_string, LCD_Command_header, server->ret).");
      Update_interface_Sign = 0;	// 启动界面刷新跟随(不能启动，等待数据)
      Update_Sign = 0;
      Filter_change_Receive_data_buffer(&head, LCD_Command_header, strlen(LCD_Command_header), Start_Receive_data_buffer);
    }
    Follow_pointer = head; 	// 拉指针

  }
  // 常规数据 
  else {
    MSYSLOG("MT", "Enter general data.");
    // 中间数据
    if(NULL == head) {
      MSYSLOG("MT", "Enter NULL == head.");
      // 头
      Filter_change_Receive_data_buffer(&head, LCD_Command_header, strlen(LCD_Command_header), Start_Receive_data_buffer);
      Follow_pointer = head;
      Update_interface_Sign = 0;
      Interface_pointer = head;
      Update_Sign = 0;	// 拉指针
    }
    // 判断新增还是扩列
    if(NULL == Follow_pointer->next) {// 新增
      MSYSLOG("MT", "Enter NULL == Follow_pointer->next.");
      Filter_change_Receive_data_buffer(&Follow_pointer->next, server->recvline, server->ret, Continue_Receive_data_buffer);
      Follow_pointer = Follow_pointer->next;
      Update_interface_Sign = 1;
    } 
    else {	// 非新增
      MSYSLOG("MT", "Enter not NULL == Follow_pointer->next.");
      if( !strncmp(Follow_pointer->next->Data_string, server->recvline, server->ret) ) {
        MSYSLOG("MT", "Enter !strncmp(Follow_pointer->next->Data_string, server->recvline, server->ret).");
        //  数据未变
        Follow_pointer = Follow_pointer->next;
      }
      else {
        MSYSLOG("MT", "Enter not !strncmp(Follow_pointer->next->Data_string, server->recvline, server->ret).");
        // 数据更改
        Filter_change_Receive_data_buffer(&Follow_pointer->next, server->recvline, server->ret, Continue_Receive_data_buffer);
        Follow_pointer = Follow_pointer->next;
        Update_interface_Sign = 1;
      }
    }
  }
  if(0 == Update_interface_Sign) {
    MSYSLOG("MT", "Enter 0 == Update_interface_Sign.");
    Interface_pointer = head;
    Update_Sign = 0;
  }
  if(1 == Update_interface_Sign) {
    MSYSLOG("MT", "Enter 1 == Update_interface_Sign.");
    if(0 == Update_Sign) {	// 起头
      MSYSLOG("MT", "Enter 0 == Update_Sign.");
      // 临时方案 合并数据头（0 0 0 0,0 和 0 0 64,128,0）两条指令 
      interface_Pixel_unit(Interface, 0);        // 0 0 64,128,0
      Filter_refresh_Receive_data_buffer(Interface, parsing, Interface_pointer->Data_string);
      Update_Sign = 1;
    }
    do {
      MSYSLOG("MT", "Enter do while(Interface_pointer != Follow_pointer).");
      Filter_refresh_Receive_data_buffer(Interface, parsing, (Interface_pointer->next->Data_string));
      Interface_pointer = Interface_pointer->next;
    } while(Interface_pointer != Follow_pointer);
    lcd_interface_refresh(Interface);
  }
}

// pri_terminal_Pixel_overall(Interface_addr,64,128);

void pri_server_recvline_out(struct UTP_socket_server * server) {
  printf("server.recvline = %s\n", server->recvline);
  for(int count = 0; count < server->ret; count++) {
    printf("%x ", server->recvline[count]);
    printf("\n");
  }
}

int main(int argc, char* argv[]) {
  if(argv[1])
    if(!strcmp(argv[1], "-v")) {
      printf (
          "v1.0\n"
          );
      return 0;
    }
  initial_lcd();							            //!y drive lcd

  struct Interface_Pixel_overall Interface;
  init_interface(&Interface);

  struct UTP_socket_server server;
  com_UTP_socket_server(&server);
  struct Instruction parsing;

  set_lcd_interface_refresh_time_Refresh_Sign();

  while(1) {
    bzero(&server.recvline, sizeof(server.recvline));
    server.ret = recvfrom(server.sockfd, server.recvline, sizeof(server.recvline), 0, 
        (struct sockaddr*)&server.presaddr, &server.len);
    if (server.ret <= 0) {		// 接受有问题
    } 
    else {
      // 过滤-》解指令-》字体类型转化-》解字模-》刷Interface-》输出 Interface
      Filter_header_Receive_data_buffer(&Interface, &parsing, &server);
    }
  }
  return 0;
}
