#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
KEEP int exercise(int n){
    int scaled=n*5-2;
    int quotient=scaled/4;
    int rest=scaled%4;
    return quotient+rest;
}
