@echo off
setlocal EnableExtensions

set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..

py "%SCRIPT_DIR%security_checks.py" --repo-root "%REPO_ROOT%" %*
exit /b %ERRORLEVEL%
