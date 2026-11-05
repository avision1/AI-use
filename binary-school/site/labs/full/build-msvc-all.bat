@echo off
setlocal
cd /d "%~dp0"
if "%VSCMD_ARG_TGT_ARCH%"=="" (echo Open an x86 or x64 Native Tools Command Prompt first.& exit /b 1)
set "LAB_OUT=msvc-%VSCMD_ARG_TGT_ARCH%"
if not exist "%LAB_OUT%" mkdir "%LAB_OUT%"
for %%N in (constructs calls records patch_logic obfuscation audit windows_lab) do (
 cl /nologo /TC /W4 /Od /Zi /FAs /Fa"%LAB_OUT%\%%N.asm" /Fo"%LAB_OUT%\%%N.obj" /Fd"%LAB_OUT%\%%N.pdb" /Fe"%LAB_OUT%\%%N.exe" %%N.c
 if errorlevel 1 exit /b 1
 cl /nologo /TC /W4 /O2 /Fo"%LAB_OUT%\%%N-opt.obj" /Fe"%LAB_OUT%\%%N-opt.exe" %%N.c
 if errorlevel 1 exit /b 1
)
cl /nologo /TC /Od /c /FAs /Fa"%LAB_OUT%\leaf.asm" /Fo"%LAB_OUT%\leaf.obj" leaf.c
