#ifndef _GIT_DATA_H_
#define _GIT_DATA_H_

#include <stdio.h>
#include <strings.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>


//---------------------------------------------------
struct UTP_socket_server{
	int sockfd;
	int ret;
	socklen_t len;
	char recvline[1024];
	struct sockaddr_in saddr;
	struct sockaddr_in presaddr;
};
void com_UTP_socket_server(struct UTP_socket_server *server);
//---------------------------------------------------
// 解析
struct Instruction{
	int x;
	int y;
	int mode;
	char buf[1024];
};
// 数据分发
int Instruction_parsing_add_load(int parsing_addr,int buf_add,int status);
// 解包 返回地址
int Instruction_parsing_Split(int addr,int instruction_buf,char segmentation);
// 数据解析
void Instruction_parsing_char(char *server_char_addr, struct Instruction *parsing, char segmentation);
// 打印
void pri(int parsing_addr);

#endif
