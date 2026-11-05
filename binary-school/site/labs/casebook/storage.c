#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
int stored=17;
KEEP int exercise(int n){
    int local=n+5;
    stored+=2;
    return local+stored;
}
