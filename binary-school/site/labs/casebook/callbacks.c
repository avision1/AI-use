#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
typedef int (*Operation)(int);
KEEP int rise(int x){return x+6;}
KEEP int twice(int x){return x*2;}
KEEP int lower(int x){return x-3;}
Operation operations[3]={rise,twice,lower};
KEEP int exercise(int n){
    if(n<0)return -9;
    return operations[n%3](n);
}
