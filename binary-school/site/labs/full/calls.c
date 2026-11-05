#include <stdio.h>
#if defined(_MSC_VER) && defined(_M_IX86)
#define CDECL __cdecl
#define STDCALL __stdcall
#define FASTCALL __fastcall
#else
#define CDECL
#define STDCALL
#define FASTCALL
#endif
int CDECL add_two(int a,int b){
return a+b;
}

int STDCALL add_std(int a,int b){
return a+b;
}

int FASTCALL add_fast(int a,int b){
return a+b;
}

int seven(int a,int b,int c,int d,int e,int f,int g){
return a+b+c+d+e+f+g;
}

int fact(int n){
if(n<=1)return 1;
return n*fact(n-1);
}

int main(void){
printf("add=%d std=%d fast=%d\n",add_two(4,9),add_std(4,9),add_fast(4,9));
printf("seven=%d fact=%d\n",seven(1,2,3,4,5,6,7),fact(5));
return 0;
}

