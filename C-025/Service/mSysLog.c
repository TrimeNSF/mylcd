/*************************************************************************
    > Author: LaiQiMing
    > Mail: 13536343225@139.com
 ************************************************************************/

#include "mSysLog.h"

void mSysLog(const char *func, const char *file, const int line,
    const char *type, const char *format, ...) {

  static Time_info ts;
  struct timeval tv;
  struct tm *local;
  gettimeofday(&tv, NULL);
  //mSysLog(0, "tv.tv_sec = %d\n", tv.tv_sec);
  ts.timestamp = tv.tv_sec;
  local = localtime(&tv.tv_sec);
  ts.day = local->tm_mday;
  sprintf(ts.date, "%04d-%02d-%02d", local->tm_year+1900,local->tm_mon+1,local->tm_mday);
  sprintf(ts.time, "%02d:%02d:%02d.%.6ld", local->tm_hour,local->tm_min,local->tm_sec,tv.tv_usec);

  va_list a_p; //args_point
  va_start(a_p, format);
  char fmt_str[2048] = {0};
  vsnprintf(fmt_str, sizeof(fmt_str), format, a_p);
  va_end(a_p);

  //printf ("[%s %s #%d] %s -- %s@%s:%d: %s", ts.date, ts.time, getpid(), type, func, file, line, fmt_str);
  printf ("[%s %s #%d] %s %s:%d -- : %s\n", ts.date, ts.time, getpid(), type, file, line, fmt_str);
  fflush(stdout);

}

void hex_dump(void *msg, int msg_len) {
  int i = 0;
  char hexstr[49] = {0}, ascstr[17] = {0}, buf[3] = {0};
  unsigned char b = 0, dumpstr = 0;
  char *pMsg = msg;
  memset (hexstr, ' ', 48);
  hexstr[48] = '\0';
  memset (ascstr, ' ', 16);
  ascstr[16] = '\0';

  MSYSLOG("DEBUG", "HEX                                              ASCII");
  for(i = 0; i < msg_len; i++) {
    b = pMsg[i];
    sprintf(buf, "%02x", b);
    hexstr[i%16*3]   = buf[0];
    hexstr[i%16*3+1] = buf[1];
    hexstr[i%16*3+2] = ' ';
    ascstr[i%16] = (b > 31 && b < 128) ? b : '.';
    if((dumpstr = ((i+1)%16 == 0)) != 0) {
      MSYSLOG("DEBUG", "%48s %16s", hexstr, ascstr);
      if(i < (msg_len - 1)) {
        memset(hexstr, ' ', 48);
        memset(ascstr, ' ', 16);
      }
    }
  }
  if(!dumpstr)
    MSYSLOG("DEBUG", "%48s %16s", hexstr, ascstr);
  return;
}

