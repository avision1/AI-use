@echo off
setlocal
cd /d "%~dp0"
if "%VSCMD_ARG_TGT_ARCH%"=="" (echo Use an x86 or x64 Native Tools developer prompt.& exit /b 1)
set "CASE_OUT=msvc-%VSCMD_ARG_TGT_ARCH%"
if not exist "%CASE_OUT%" mkdir "%CASE_OUT%"
pushd "%CASE_OUT%"
for %%C in (storage arithmetic branches loops arguments switch records callbacks) do (
 cl /nologo /TC /W4 /Od /Zi /FAs /Fe:%%C.exe ..\%%C.c ..\driver.c
 if errorlevel 1 (popd & exit /b 1)
)
popd
