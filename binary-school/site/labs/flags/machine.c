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
  volatile unsigned bits=0x5a; int target=(int)((bits>>1)^0x13);
  return input == target;
}
NOINLINE void accepted(void) {
  unsigned char encoded[]={ 123,106,66,84,88,90,81,80,87,92,102,10,8,1,92,91,12,12,95,13,9,68 };
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
