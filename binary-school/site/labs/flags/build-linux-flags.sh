#!/bin/sh
set -eu
cd "$(dirname "$0")"
for course in assembly foundations machine patterns calls ghidra types debug dynamic windows anti workshop secure; do
 gcc -std=c11 -Wall -Wextra -g -O0 "$course.c" -o "$course-guided-linux-x64"
 gcc -std=c11 -Wall -Wextra -O2 "$course.c" -o "$course-independent-linux-x64"
 strip "$course-independent-linux-x64"
done
