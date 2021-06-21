#include <stdio.h>
 #include <stdlib.h>


#define unit_length         			16
#define  ope_File_pathname            "./GB2312_ascii_13.dat"
#define ope_File_mode                       "rb"

struct File_access_data{
    FILE* open_fd;
    int git_data_length;
    unsigned char buf[unit_length];
};

#define pointer         long
//=======================================================================================================================================
void open_data(pointer addr){
    struct File_access_data *File_access = (struct File_access_data *)addr;
    File_access->open_fd = fopen(ope_File_pathname,ope_File_mode);
    File_access->git_data_length = unit_length;
}
void retrieve_data(pointer addr,int data){
    struct File_access_data * File_access = (struct File_access_data *)addr;
    printf("000000000000000000000000 =  %d\n",data);
    fseek(File_access->open_fd, unit_length*data, SEEK_SET);
    printf("jikexianfeng@outlook.com\n");
    fread(File_access->buf, 1, unit_length, File_access->open_fd);
}
void close_open_fd(pointer addr){
    struct File_access_data * File_access = (struct File_access_data*)addr;
    fclose(File_access->open_fd);
    File_access->open_fd = NULL;
}

struct bit_s{
    unsigned char bit0:1;
    unsigned char bit1:1;
    unsigned char bit2:1;
    unsigned char bit3:1;
    unsigned char bit4:1;
    unsigned char bit5:1;
    unsigned char bit6:1;
    unsigned char bit7:1;
};
unsigned char H_L(unsigned char Value){
    unsigned char value;
    struct bit_s ret;

    ret.bit7 = (Value>>0)&0x01;
    ret.bit6 = (Value>>1)&0x01;
    ret.bit5 = (Value>>2)&0x01;
    ret.bit4 = (Value>>3)&0x01;
    ret.bit3 = (Value>>4)&0x01;
    ret.bit2 = (Value>>5)&0x01;
    ret.bit1 = (Value>>6)&0x01;
    ret.bit0 = (Value>>7)&0x01;

    char *p = (char *)&ret;
    value = *p;
    return value;
}
//=======================================================================================================================================
#define image_Start_position		0
#define image_End_position			8
#define image_width					8
#define image_Rows					2

void pri_single_Object_data(pointer  addr,int number){
	struct File_access_data * File_access = (struct File_access_data*)addr;
	unsigned char key[8] = {0x80,0x40,0x20,0x10,0x08,0x04,0x02,0x01};
	for(int Rows = 0; Rows < image_Rows;Rows++){
		for(int width = image_Start_position;width < image_End_position;width++){
		printf("0x%02X,",H_L(File_access->buf[Rows*image_width + width]));
		}
	}printf("\t// %d\n", number);
}
void pri_single_Object_image(pointer  addr,int number){
    struct File_access_data * File_access = (struct File_access_data*)addr;
    unsigned char key[8] = {0x80,0x40,0x20,0x10,0x08,0x04,0x02,0x01};
    int i,j,k,flag;
	for(k = 0; k < image_Rows;k++){
	    for(j = 0 ; j < 8;j++ ){
	        for(i = image_Start_position;i < image_End_position;i++){
	            flag = File_access->buf[k*image_width + i]&key[j]; printf("%s ", flag?"●":"○");
	        } printf("\n");
	    }
	}
}

void pri_File_access_file(pointer addr,int number){
	struct File_access_data * File_access = (struct File_access_data*)addr;
	unsigned char key[8] = {0x80,0x40,0x20,0x10,0x08,0x04,0x02,0x01};
	unsigned char buf[1024];
	unsigned char bufs[1024];
	unsigned char *tep = buf;
	//for(int count = 0;count < 32; count++)printf("0x%02X,",H_L(File_access->buf[count]));printf("\t// %d\n", numbe);
	for(int Rows = 0; Rows < image_Rows;Rows++){
		for(int width = image_Start_position;width < image_End_position;width++){
			tep = tep + sprintf(tep,"0x%02X,",H_L(File_access->buf[Rows*image_width + width]));
		}
	}	tep = tep + sprintf(tep,"\t// %d", number);
		sprintf(bufs,"echo \"%s\" >> data.h",buf);
		system(bufs	);
}

void pri_File_access_terminal(pointer  addr,int number){
	pri_single_Object_data(addr,number);
	pri_single_Object_image(addr,number);
}

#define out_data_terminal	0
#define out_data_FILE		1

#define out_data_purpose	out_data_terminal

#if (out_data_purpose == out_data_terminal)
#define out_data(addr,number)			pri_File_access_terminal(addr,number)
#elif(out_data_purpose == out_data_FILE) 
#define out_data(pointer,addr)			pri_File_access_file(pointer,addr)
#endif
//=============================================
int main(void){
    struct File_access_data   File_access;
    int number = 0;
    open_data((pointer)&File_access);
    while(96 - number){
        retrieve_data((pointer)&File_access,number+32);
        out_data((pointer)&File_access,number);
        number++;
    }
    close_open_fd((pointer)&File_access);
    return 0;
}


/***************************************************************************************************************************************************************************/
