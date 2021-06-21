# include <stdio.h>
# include <stdlib.h>
# include <unistd.h>
#include <string.h>
#include <stdio.h>

#define tem 0


//0 0 0 Signal,strength

// ----------------------------------
void Signal_strength_indicator(int x,int y,int strength){
	char buf[64];
	char count;
	memset(buf,0,sizeof(buf));sprintf(buf,"./client %d %d 4 %d,%d,%d",x*8,y*6,x*8+8,y*6+12,0);system(buf);usleep(tem);			// 清屏
	// 信号强度
	if(strength > 1)memset(buf,0,sizeof(buf));sprintf(buf,"./client %d %d 4 %d,%d,%d",x*8+14-8,y*6+1,x*8+7,y*6+2,1);system(buf);usleep(tem);		// 一格
	if(strength > 2)memset(buf,0,sizeof(buf));sprintf(buf,"./client %d %d 4 %d,%d,%d",x*8+13-8,y*6+3,x*8+7,y*6+4,1);system(buf);usleep(tem);		// 一格
	if(strength > 3)memset(buf,0,sizeof(buf));sprintf(buf,"./client %d %d 4 %d,%d,%d",x*8+12-8,y*6+5,x*8+7,y*6+6,1);system(buf);usleep(tem);		// 一格
	if(strength > 4)memset(buf,0,sizeof(buf));sprintf(buf,"./client %d %d 4 %d,%d,%d",x*8+11-8,y*6+7,x*8+7,y*6+8,1);system(buf);usleep(tem);		// 一格
	if(strength > 5)memset(buf,0,sizeof(buf));sprintf(buf,"./client %d %d 4 %d,%d,%d",x*8+10-8,y*6+9,x*8+7,y*6+10,1);system(buf);usleep(tem);	    // 一格
	if(strength > 6)memset(buf,0,sizeof(buf));sprintf(buf,"./client %d %d 4 %d,%d,%d",x*8+9-8,y*6+11,x*8+7,y*6+12,1);system(buf);usleep(tem);	    // 一格
}

int main(void){
	system("./client 0 0 4 64,128,0");usleep(tem);	// 清屏
	system("./client 0 0 0 0,0");usleep(tem);		// 数据头指令
#if 0
	Signal_strength_indicator(0,19,6);            // 更改界面样式
#else
	// x y mode sub_bode,parameter
	// x y 5 0,strength
	system("./client 0 0 5 0,5");usleep(tem);		// 数据头指令
#endif
	return 0;
}

