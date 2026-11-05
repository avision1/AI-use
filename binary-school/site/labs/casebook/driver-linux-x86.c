int exercise(int);
static void output(const char *p,unsigned n){int r;__asm__ volatile("int $0x80":"=a"(r):"0"(4),"b"(1),"c"(p),"d"(n):"memory");}
__attribute__((noreturn)) static void end(int code){__asm__ volatile("int $0x80"::"a"(1),"b"(code):"memory");__builtin_unreachable();}
void launch(unsigned *stack){
 unsigned argc=stack[0];char **argv=(char**)(stack+1);
 if(argc!=2)end(2);
 const char *p=argv[1];int sign=1,n=0;
 if(*p=='-'){sign=-1;++p;}
 if(!*p)end(2);
 while(*p){if(*p<'0'||*p>'9')end(2);n=n*10+(*p++-'0');if(n>20)end(2);}
 int value=exercise(sign*n);
 output("result=",7);
 char digits[16];unsigned count=0;unsigned magnitude;
 if(value<0){output("-",1);magnitude=0u-(unsigned)value;}else magnitude=(unsigned)value;
 do{digits[count++]=(char)('0'+magnitude%10);magnitude/=10;}while(magnitude);
 while(count)output(&digits[--count],1);
 output("\n",1);end(0);
}
