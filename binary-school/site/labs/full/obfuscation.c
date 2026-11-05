#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
int flattened(int x){
volatile int state=0;
int y=0;
while(state!=3){
switch(state){
case 0:y=x*3;
state=1;
break;
case 1:y+=7;
state=3;
break;
default:state=3;
break;
}
}
return y;
}

void message(void){
unsigned char data[]={
0x6C,0x61,0x62,0x7F,0x6F,0x6B,0}
;
char out[7];
int i;
for(i=0;
i<6;
i++)out[i]=(char)(data[i]^0x20);
out[6]=0;
puts(out);
}

int main(int argc,char **argv){
char *end;
long x;
if(argc!=2)return 2;
errno=0;
x=strtol(argv[1],&end,10);
if(errno||end==argv[1]||*end||x< -100||x>100)return 2;
message();
printf("score=%d\n",flattened((int)x));
return 0;
}

