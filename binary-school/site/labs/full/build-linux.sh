#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
for name in constructs calls records patch_logic obfuscation audit; do
 gcc -fdebug-prefix-map="$PWD"=. -std=c11 -Wall -Wextra -g -O0 "$name.c" -o "$name-O0"
 gcc -fdebug-prefix-map="$PWD"=. -std=c11 -Wall -Wextra -O2 "$name.c" -o "$name-O2"
 cp "$name-O2" "$name-stripped"
 strip "$name-stripped"
done
gcc -m32 -O0 -S -masm=intel leaf.c -o leaf-x86.s
gcc -m64 -O0 -S -masm=intel leaf.c -o leaf-x64.s
gcc -fdebug-prefix-map="$PWD"=. -g -O1 -fno-omit-frame-pointer -fsanitize=address,undefined audit.c -o audit-san
gcc -fdebug-prefix-map="$PWD"=. -g -O0 misdirection-driver.c misdirection.S -o misdirection-gcc
echo "Built Linux artifacts. Native Windows targets require MSVC on Windows."
