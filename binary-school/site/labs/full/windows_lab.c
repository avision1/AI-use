#include <windows.h>
#include <stdio.h>
int transform(int x){
return x*3+7;
}

int main(void){
const wchar_t *wide=L"Windows lab";
puts("WINDOWS_TRAINING");
printf("pid=%lu wide_length=%d\n",(unsigned long)GetCurrentProcessId(),lstrlenW(wide));
if(IsDebuggerPresent()){
puts("DEBUG_PATH");
return 2;
}
printf("score=%d\n",transform(4));
return 0;
}

