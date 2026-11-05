.text
.globl _start
_start:
 mov %esp,%eax
 and $-16,%esp
 sub $12,%esp
 push %eax
 call launch
 ud2
.section .note.GNU-stack,"",@progbits
