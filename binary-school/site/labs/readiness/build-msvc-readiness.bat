@echo off
setlocal
cd /d "%~dp0"
if "%VSCMD_ARG_TGT_ARCH%"=="" (echo Open an x86 or x64 Native Tools Command Prompt.& exit /b 1)
set "LAB_OUT=msvc-%VSCMD_ARG_TGT_ARCH%"
if not exist "%LAB_OUT%" mkdir "%LAB_OUT%"
for %%S in (sources\*.c) do (
 cl /nologo /TC /W4 /Od /Zi /Fo"%LAB_OUT%\%%~nS.obj" /Fd"%LAB_OUT%\%%~nS-compile.pdb" /Fe"%LAB_OUT%\%%~nS.exe" "%%S"
 if errorlevel 1 exit /b 1
)
echo Built native MSVC programs. Repeat from the other architecture prompt to compare.
