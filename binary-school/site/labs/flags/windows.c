#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#if defined(_MSC_VER)
#define NOINLINE __declspec(noinline)
#else
#define NOINLINE __attribute__((noinline))
#endif
struct Record { short tag; int count; int bonus; };
NOINLINE int combine(int a,int b) { return a*3+b; }
NOINLINE int selection(int n) { switch(n){case 1:return 12;case 2:return 31;case 3:return 55;default:return -1;} }
NOINLINE int gate(int input) {
  uint32_t width=sizeof(uint32_t)*8u; int target=(int)width+5;
  return input == target;
}
NOINLINE void accepted(void) {
  unsigned char encoded[]={ 123,106,66,78,80,87,93,86,78,74,102,9,1,93,9,14,10,14,88,91,8,68 };
  char output[sizeof(encoded)+1];
  for(size_t i=0;i<sizeof(encoded);++i) output[i]=(char)(encoded[i]^57);
  output[sizeof(encoded)]=0;
  puts(output);
}
int main(int argc,char **argv) {
  char *end;long input;
  if(argc!=2){puts("Usage: challenge INTEGER (-100..100)");return 2;}
  errno=0;input=strtol(argv[1],&end,10);
  if(errno||end==argv[1]||*end||input< -100||input>100){puts("Invalid input");return 2;}
  if(gate((int)input)){accepted();return 0;}
  puts("Not yet. Inspect gate and try again.");return 1;
}
