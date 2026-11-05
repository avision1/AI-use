.text
.globl after_jump
.type after_jump,@function
after_jump:
 jmp .Lreal
 .byte 0xe8,0xff,0xff,0xff,0x7f
.Lreal:
 mov $17,%eax
 ret
.size after_jump,.-after_jump
.section .note.GNU-stack,"",@progbits
