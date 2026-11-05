#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#if defined(_MSC_VER)
#define NOINLINE __declspec(noinline)
#else
#define NOINLINE __attribute__((noinline))
#endif
NOINLINE int fee(int x){
return x*3+7;
}

int main(int argc,char **argv){
long n;
char *end;
if(argc!=2)return 2;
errno=0;
n=strtol(argv[1],&end,10);
if(errno||end==argv[1]||*end||n< -10||n>10)return 2;
printf("fee=%d\n",fee((int)n));
return 0;
}

