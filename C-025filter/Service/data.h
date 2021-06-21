#ifndef	__GB2312_
#define	__GB2312_

#include <stdio.h>
#include <unistd.h>
#include <wiringPi.h>

//========================================================
#define uchar unsigned char
//横向取模，字节不倒序
extern uchar const ascii_table_5x8[95][5];
extern uchar const ascii_table_6x12[95][12];
extern uchar const ascii_table_8x16[95][16];
extern uchar const GB2312_13_data_code[][24];

#endif

