/* Original Binary School training program. Bounded inputs; no system changes. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <stddef.h>
#if defined(_MSC_VER)
#define NOINLINE __declspec(noinline)
#else
#define NOINLINE __attribute__((noinline))
#endif
static int integer(const char *s, int *v) {
    char *end; long x; errno=0; x=strtol(s,&end,10);
    if(errno || end==s || *end || x < -100 || x > 100) return 0;
    *v=(int)x; return 1;
}

#ifdef _WIN32
#include <windows.h>
#endif
typedef struct {int threshold; int rate; int bonus;} Policy;
volatile int adjustment=1;
NOINLINE int charge(int n,const Policy *p) {
    int i,total=0;
    for(i=0;i<n;i++) total+=i<p->threshold?p->rate:p->rate+2;
    if(n>p->threshold) total-=p->bonus;
    return total+adjustment;
}
NOINLINE int unlock(const char *text,int probe) {
    static const unsigned char bytes[]={0x5d,0x5c,0x55,0x4d,0x58}; char word[6]; int i;
    if(probe) return -1;
    for(i=0;i<5;i++) word[i]=(char)(bytes[i]^57);
    word[5]=0; return strcmp(text,word)==0;
}
int main(int argc,char **argv) {
    Policy p={2,6,7}; int n,probe;
    if(argc!=4||!integer(argv[1],&n)||!integer(argv[3],&probe)||n<0||n>8) return 2;
#ifdef _WIN32
    printf("wide_length=%d pid=%lu\n",lstrlenW(L"Fresh task"),(unsigned long)GetCurrentProcessId());
#endif
    if(unlock(argv[2],probe)!=1) {puts("LOCKED");return 3;}
    printf("charge=%d\n",charge(n,&p));return 0;
}
