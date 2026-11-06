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

NOINLINE int accumulate(const int *xs,int count) {
    int i,total=4;
    for(i=0;i<count;i++) {
        int delta=xs[i]*(i+1);
        if(xs[i]<0) total-=delta; else total+=delta;
    }
    return total;
}
int main(int argc,char **argv) {
    int xs[3],i,total;
    if(argc!=4) return 2;
    for(i=0;i<3;i++) if(!integer(argv[i+1],&xs[i])) return 2;
    total=accumulate(xs,3); printf("total=%d\n",total);
    if(total==25 && xs[1]<0) {puts("BS{practical_watchpoint}"); return 0;} return 1;
}
