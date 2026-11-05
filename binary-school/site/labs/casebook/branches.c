#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
KEEP int exercise(int n){
    if(n<0){
        return -2;
    }else if(n<6){
        return n+9;
    }else{
        return n-4;
    }
}
