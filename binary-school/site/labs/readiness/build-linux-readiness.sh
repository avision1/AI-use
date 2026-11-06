#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p local-linux
for source in sources/*.c; do
 name=$(basename "$source" .c)
 [ "$name" = windows ] && continue
 gcc -std=c11 -Wall -Wextra -g -O0 -o "local-linux/$name" "$source"
done
