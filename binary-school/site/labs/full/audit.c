#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
/* Intentionally invalid reads ONLY in unsafe mode. Use this local training program. */
int main(int argc,char **argv){
int data[4]={
10,20,30,40}
;
long n;
char *end;
if(argc!=3)return 2;
errno=0;
n=strtol(argv[2],&end,10);
if(errno||end==argv[2]||*end||n< -100||n>100)return 2;
if(strcmp(argv[1],"unsafe")&&strcmp(argv[1],"safe"))return 2;
if(!strcmp(argv[1],"safe")&&(n<0||n>=4)){
puts("REJECT");
return 2;
}
printf("value=%d\n",data[n]);
return 0;
}

