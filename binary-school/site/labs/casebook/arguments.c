#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
KEEP int blend(int a,int b,int c,int d,int e,int f,int g,int h){
    return a+2*b-c+d-e+f-g+h;
}
KEEP int exercise(int n){
    return blend(n,11,5,13,7,17,19,23);
}
