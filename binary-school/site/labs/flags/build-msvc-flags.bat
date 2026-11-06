@echo off
setlocal
cd /d "%~dp0"
if "%VSCMD_ARG_TGT_ARCH%"=="" (echo Open an x86 or x64 Native Tools Command Prompt.& exit /b 1)
set "FLAG_OUT=msvc-%VSCMD_ARG_TGT_ARCH%"
if not exist "%FLAG_OUT%" mkdir "%FLAG_OUT%"
for %%N in (assembly foundations machine patterns calls ghidra types debug dynamic windows anti workshop secure) do (
 cl /nologo /TC /Od /Zi /Fo"%FLAG_OUT%\%%N.obj" /Fd"%FLAG_OUT%\%%N-compile.pdb" /Fe"%FLAG_OUT%\%%N.exe" %%N.c
 if errorlevel 1 exit /b 1
)
