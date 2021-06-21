#include <stdio.h>
#include <strings.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
// 打包
struct UTP_socket_client{
  int sockfd;
  int length;
	struct sockaddr_in des_addr;
  char sendline[1024];
};

void com_UTP_socket_client(int addr){
  struct UTP_socket_client *client = (struct UTP_socket_client *)addr;
  client->sockfd = socket(AF_INET, SOCK_DGRAM, 0);
  bzero(&(client->des_addr), sizeof(client->des_addr));
  client->des_addr.sin_family = AF_INET;
  client->des_addr.sin_addr.s_addr = inet_addr("127.0.0.1"); //广播地址
  client->des_addr.sin_port = htons(58471);
}

const int on = 1;
void UTP_socket(int addr){
    //char * addrs = "0 0 4 64,128,1";
    char * addrs = "0 0 3 jikexianfeng\n123456798\nzxczx";
  struct UTP_socket_client *client = (struct UTP_socket_client *)addr;
	setsockopt(client->sockfd, SOL_SOCKET, SO_BROADCAST, &(on), sizeof(on)); //设置套接字选项
	//client->length = sendto(client->sockfd, client->sendline, strlen(client->sendline), 0, (struct sockaddr*)&(client->des_addr), sizeof(client->des_addr));
	client->length = sendto(client->sockfd, addrs, strlen(addrs), 0, (struct sockaddr*)&(client->des_addr), sizeof(client->des_addr));
	if (client->length <= 0)
	{
		perror("");
		exit(-1);
	}
//	printf("finish = %d\n",client->length);
}

// x,y,buf,(0,为清屏，数据为5*8,2为8*16)

int main(int argc, char *argv[]){
  int length = 0;
  int count = 0;
  struct UTP_socket_client client;
  char *temp = NULL;
  // 数据拼接
  bzero(&(client.sendline), sizeof(client.sendline));
  for(count = 1; count < argc;count++){
    length += sprintf((client.sendline+length),"%s ",argv[count]);
  }*(client.sendline+length-1) = '\0';
  printf("sizeof(client.sendline) = %d \n",sizeof(client.sendline));

  if(0 == strlen(client.sendline));
  else
  {
    com_UTP_socket_client((int)&client);
    UTP_socket((int)&client);
  }
	return 0;
}
