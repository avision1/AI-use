#!/bin/sh
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)" || exit 1
for binary_school_python in python3 python; do
    if command -v "$binary_school_python" >/dev/null 2>&1 && "$binary_school_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
        exec "$binary_school_python" start.py "$@"
    fi
done
printf '%s\n' 'Python 3.8 or newer is required.' 'Install Python 3 from python.org (macOS) or your distribution package manager (Linux).'
exit 1
