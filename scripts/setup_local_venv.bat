@echo off
setlocal EnableExtensions

echo Setting Python Env

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
set "CLI_ENTRY=%REPO_ROOT%\cli\main.py"
set "VENV_DIR=%REPO_ROOT%\.venv"

if not exist "%CLI_ENTRY%" (
  echo Could not find CLI entrypoint: %CLI_ENTRY%
  exit /b 1
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
  set "PYTHON_BIN=py"
) else (
  where py >nul 2>nul
  if %ERRORLEVEL% equ 0 (
    set "PYTHON_BIN=py"
  ) else (
    echo Could not find python or py on PATH.
    exit /b 1
  )
)

pushd "%REPO_ROOT%"
%PYTHON_BIN% "%CLI_ENTRY%" setup-venv --venv "%VENV_DIR%" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %EXIT_CODE%
