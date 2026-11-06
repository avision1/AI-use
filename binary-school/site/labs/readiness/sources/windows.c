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
typedef struct {char label[8]; int quantity; int unit_price;} Order;
NOINLINE int quote(const Order *o) {return o->quantity*o->unit_price+(o->quantity<3?5:0);}
int main(int argc,char **argv) {
    Order order={"LAB",0,7}; const wchar_t *wide=L"Inspect me"; int q;
    if(argc!=3 || !integer(argv[2],&q) || q<0 || q>10) return 2;
    printf("pid=%lu wide_length=%d\n",(unsigned long)GetCurrentProcessId(),lstrlenW(wide));
    if(IsDebuggerPresent()) {puts("DEBUG_PATH: inspect this return and repeat without debugging");return 3;}
    if(lstrcmpA(argv[1],order.label)!=0) return 1;
    order.quantity=q; printf("quote=%d\n",quote(&order));
    if(q==4) {puts("BS{practical_pe_imports}");return 0;} return 1;
}
#else
#error This investigation is a native Windows PE. Build with MSVC or MinGW-w64.
#endif
