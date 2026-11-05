#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
int global_count=3;

int visit(int x){
static int visits=0;
int local=x+global_count;
++visits;
return local+visits;
}

int sum_odd(int n){
int s=0;
for(int i=0;
i<n;
i++){
if(i==7)break;
if((i&1)==0)continue;
s+=i;
}
return s;
}

int choose(int x){
switch(x){
case 2:return 11;
case 3:return 40;
case 4:return 9;
case 5:return 72;
default:return -1;
}
}

int main(int argc,char **argv){
char *end;
long n;
if(argc!=2)return 2;
errno=0;
n=strtol(argv[1],&end,10);
if(errno||*end||end==argv[1]||n< -100||n>100)return 2;
printf("visit1=%d\n",visit((int)n));
printf("visit2=%d\n",visit((int)n));
printf("sum=%d\nchoose=%d\n",sum_odd((int)n),choose((int)n));
return 0;
}

