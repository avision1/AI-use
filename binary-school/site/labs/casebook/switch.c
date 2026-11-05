#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
KEEP int op_a(int x){return x+8;}
KEEP int op_b(int x){return x*4;}
KEEP int op_c(int x){return x*x+3;}
KEEP int exercise(int n){
    switch(n){
        case 0:return op_a(n);
        case 1:return op_b(n);
        case 2:return op_c(n);
        case 3:return op_a(n+2);
        case 4:return op_c(n-1);
        default:return -7;
    }
}
