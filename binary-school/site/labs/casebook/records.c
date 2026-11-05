#if defined(_MSC_VER)
#define KEEP __declspec(noinline)
#else
#define KEEP __attribute__((noinline))
#endif
struct Entry{unsigned char group; int quota; short bonus;};
struct Entry entries[3]={{'M',8,3},{'N',13,-2},{'P',21,4}};
KEEP int exercise(int n){
    if(n<0 || n>=3)return -8;
    return entries[n].quota+entries[n].bonus;
}
