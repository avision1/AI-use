#include <stdio.h>
#include <stdlib.h>
int transform(int x) { return x * 3 + 7; }
int array_total(void) { int a[4]={2,4,6,8}; int sum=0; for(int i=0;i<4;i++) sum+=a[i]; return sum; }
int main(int argc,char **argv) { int x=argc>1?atoi(argv[1]):4; puts("BINARY_SCHOOL"); printf("result=%d\n",transform(x)); puts(x==23?"ACCESS_OK":"TRY_AGAIN"); printf("total=%d\n",array_total()); return 0; }
