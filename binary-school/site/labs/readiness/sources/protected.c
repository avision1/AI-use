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

static const unsigned char encoded[]={0x38,0x34,0x25,0x39,0x30};
NOINLINE int decode_and_compare(const char *s) {
    char key[6]; unsigned i,noise=17;
    for(i=0;i<5;i++) {noise=(noise*3u)^i; key[i]=(char)(encoded[i]^0x55u);}
    key[5]=0;
    /* noise is a distractor, not a data dependency of the comparison. */
    return strcmp(s,key)==0;
}
int main(int argc,char **argv) {
    int probe;
    if(argc!=3 || !integer(argv[2],&probe)) return 2;
    /* Explicit toy probe: no real process inspection and no timing dependency. */
    if(probe!=0) {puts("ANALYSIS_PATH");return 3;}
    if(!decode_and_compare(argv[1])) return 1;
    puts("BS{practical_decoding}");return 0;
}
