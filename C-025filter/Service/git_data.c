#include <stdio.h>
#include <strings.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include "git_data.h"

// 设置
void com_UTP_socket_server(struct UTP_socket_server *server) {
  server->sockfd = socket(AF_INET, SOCK_DGRAM, 0);
  bzero(&server->saddr, sizeof(server->saddr));
  server->saddr.sin_family = AF_INET;
  server->saddr.sin_addr.s_addr = inet_addr("127.0.0.1");
  server->saddr.sin_port = htons(58471);
  bind(server->sockfd, (struct sockaddr*)&server->saddr, sizeof(server->saddr));
}
// 分支
#define add_load_x		0
#define add_load_y		1
#define add_load_mode	2
#define add_load_char   3

int Instruction_parsing_add_load(int parsing_addr,int buf_add,int status){
  struct Instruction* parsing = (struct Instruction*)parsing_addr;
  char *buf = (char *)buf_add;
  int ret;
  switch (status) {
    case add_load_x:{
                      parsing->x = atoi(buf);ret = add_load_y;
                    }break;
    case add_load_y:{
                      parsing->y = atoi(buf);ret = add_load_mode;
                    }break;
    case add_load_mode:{
                         parsing->mode = atoi(buf);ret = add_load_char;
                       }break;
    case add_load_char:{ret = add_load_x;
                         // 解析 字符串 (已经加载完成)
                       }break;
    default :{ret = add_load_x;}break;
  }
  return ret;
}

// 解包 返回地址
int Instruction_parsing_Split(int addr,int instruction_buf,char segmentation){
  int count = 0;													// 长度统计
  char * recvline = (char *)(addr);				//
  char * buf = (char *)(instruction_buf);
  //	printf("%s\n",recvline);
  //	printf("*(recvline+count) = %d\n",*(recvline+count));
  while(('\0' != *(recvline+count))&(segmentation != *(recvline+count))){
    *(buf+count) = *(recvline+count);
    count++;
  }count++;
  return count;
}
//==========================================================================
// 数据解析
void Instruction_parsing_char(char *server_char_addr, struct Instruction *parsing, char segmentation){
  char *p = server_char_addr;
  int status = add_load_x;			// 数据状态
  int data_addr = 0;	// 解包地址
  int AT_Number_instructions  = 0;
  // 开始解析
  do{
    bzero(&parsing->buf, sizeof(parsing->buf));		// 数据 清理
    //		while(segmentation == *p)p++;		// 处理多余的segmentation
    if(3 == AT_Number_instructions)data_addr = Instruction_parsing_Split((int)(p),(int)&(parsing->buf),0);
    else data_addr = Instruction_parsing_Split((int)(p),(int)&(parsing->buf),segmentation);	// 解包
    AT_Number_instructions = AT_Number_instructions + 1;
    p = p + data_addr; 	// 地址偏移
    // 系统状态
    status = Instruction_parsing_add_load((int)(parsing),(int)&(parsing->buf),status);
  }while(('\0' != *p)&(4 != AT_Number_instructions));		// 字符串结尾
}
void pri(int parsing_addr){
  struct Instruction* parsing = (struct Instruction*)parsing_addr;
  printf("parsing->x = %d\n",parsing->x);
  printf("parsing->y = %d\n",parsing->y);
  printf("parsing->mode = %d\n",parsing->mode);
  printf("parsing->buf = %s\n",parsing->buf);
}
