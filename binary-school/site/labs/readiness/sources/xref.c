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

NOINLINE int dispatch(const char *name, int n) {
    static const int weights[4]={3,7,2,5};
    int i,total=0;
    if(strcmp(name,"orbit")!=0 || n<0 || n>4) return -1;
    for(i=0;i<n;i++) total+=weights[i]*(i+1);
    switch(n) {case 2: return total+4; case 3: return total-2; default: return total;}
}
int main(int argc,char **argv) {
    int n,r; if(argc!=3 || !integer(argv[2],&n)) return 2;
    r=dispatch(argv[1],n); printf("result=%d\n",r);
    if(r==21) {puts("BS{practical_xrefs}"); return 0;} return 1;
}
