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

typedef struct {uint8_t enabled; int32_t amount; int16_t bias; char name[6];} Record;
NOINLINE int score(const Record *r,int n) {
    int i,total=0; for(i=0;i<n;i++) if(r[i].enabled) total+=r[i].amount+r[i].bias;
    return total;
}
int main(int argc,char **argv) {
    int n,total; Record rows[3]={{1,12,-3,"ash"},{0,50,4,"birch"},{1,-2,7,"cedar"}};
    if(argc!=2 || !integer(argv[1],&n) || n<0 || n>3) return 2;
    total=score(rows,n); printf("total=%d\n",total);
    if(n==3 && total==14) {puts("BS{practical_records}"); return 0;} return 1;
}
