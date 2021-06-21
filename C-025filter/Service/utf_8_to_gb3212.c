#include <iconv.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utf_8_to_gb3212.h"


//*****************************************************************
int code_convert_process(char *from_charset,char *to_charset,char *inbuf,int inlen,char *outbuf,int outlen){
    iconv_t cd;
    int rc;
    char **pin = &inbuf;
    char **pout = &outbuf;
    cd = iconv_open(to_charset,from_charset);
    if (cd==0) return -1;
    memset(outbuf,0,outlen);
    if (iconv(cd,pin,&inlen,pout,&outlen)==-1) return -1;
    iconv_close(cd);
    return 0;
}

#define UTF8_to_GB3212(in_buf,in_len,out_buf,out_len)   code_convert_process(UTF_8,GB2312,in_buf,in_len,out_buf,out_len)
#define GB3212_to_UTF8(in_buf,in_len,out_buf,out_len)   code_convert_process(GB2312,UTF_8,in_buf,in_len,out_buf,out_len)
//*****************************************************************
