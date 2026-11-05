#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
KEEP int exercise(int n){
    int total=0;
    int i=0;
    while(i<n){
        total+=i+2;
        ++i;
    }
    return total;
}
