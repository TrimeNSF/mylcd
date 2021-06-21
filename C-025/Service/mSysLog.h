/*************************************************************************
    > Author: LaiQiMing
    > Mail: 13536343225@139.com
 ************************************************************************/

#ifndef _MSYSLOG_H
#define _MSYSLOG_H

#include <stdio.h>
#include<stdarg.h>
#include<string.h>
#include<time.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#define MSYSLOG(type, format, ...) mSysLog(__func__, __FILE__, __LINE__, type, format, ##__VA_ARGS__)

typedef struct
{
  char date[11];
  char time[16];
  int timestamp;
  int day;
}Time_info;

void mSysLog(const char *func, const char *file, const int line,
    const char *type, const char *format, ...);
void hex_dump(void *msg, int msg_len);

#endif
