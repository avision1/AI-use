#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
int exercise(int);
int main(int argc,char **argv){
 char *end;long n;
 if(argc!=2)return 2;
 errno=0;n=strtol(argv[1],&end,10);
 if(errno||end==argv[1]||*end||n< -20||n>20)return 2;
 printf("result=%d\n",exercise((int)n));
 return 0;
}
