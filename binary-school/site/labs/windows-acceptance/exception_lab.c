/* Original bounded MSVC/Windows SEH training program. No files or network. */
#include <windows.h>
#include <stdio.h>
#define TRAINING_EXCEPTION ((DWORD)0xE0421001u)
int main(void) {
    volatile int handled = 0;
    __try {
        RaiseException(TRAINING_EXCEPTION, 0, 0, NULL);
    } __except (GetExceptionCode() == TRAINING_EXCEPTION ?
                EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) {
        handled = 1;
    }
    printf("handled=%d\n", (int)handled);
    return handled ? 0 : 1;
}
