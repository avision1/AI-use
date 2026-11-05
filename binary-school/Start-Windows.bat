@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if not errorlevel 1 (
 py -3 start.py %*
 goto finish
)
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if not errorlevel 1 (
 python3 start.py %*
 goto finish
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if not errorlevel 1 (
 python start.py %*
 goto finish
)
echo Python 3.8 or newer is required. Install Python 3 from https://www.python.org/downloads/
echo Enable the Python launcher or PATH option during installation, then run this file again.
:finish
pause
