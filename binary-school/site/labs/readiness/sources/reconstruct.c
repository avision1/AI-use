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

typedef struct {int limit; int rate; int discount;} Plan;
NOINLINE int price(int n,const Plan *p) {
    int i,total=0;
    for(i=0;i<n;i++) total+=(i<p->limit?p->rate:p->rate+2);
    if(n>=4) total-=p->discount;
    return total;
}
int main(int argc,char **argv) {
    Plan plans[2]={{2,3,2},{3,5,4}}; int mode,n,total;
    if(argc!=3 || !integer(argv[1],&mode)||!integer(argv[2],&n)||mode<0||mode>1||n<0||n>8) return 2;
    total=price(n,&plans[mode]); printf("price=%d\n",total);
    if(mode==1 && n==5 && total==25) {puts("BS{practical_reconstruction}");return 0;} return 1;
}
