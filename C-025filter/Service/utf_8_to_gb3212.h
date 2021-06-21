#ifndef _UTF_8_TO_GB3212_
#define  _UTF_8_TO_GB3212_

//*****************************************************************
#define buf_length 128
# define UTF_8 "utf-8"
#define GB2312  "gb2312"
//*****************************************************************
int code_convert_process(char *from_charset,char *to_charset,char *inbuf,int inlen,char *outbuf,int outlen);
#define UTF8_to_GB3212(in_buf,in_len,out_buf,out_len)   code_convert_process(UTF_8,GB2312,in_buf,in_len,out_buf,out_len)
#define GB3212_to_UTF8(in_buf,in_len,out_buf,out_len)   code_convert_process(GB2312,UTF_8,in_buf,in_len,out_buf,out_len)

#endif
