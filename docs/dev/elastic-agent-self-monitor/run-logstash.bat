@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%logstash.conf"
set "OUT_DIR=%SCRIPT_DIR%out"
set "TEMP_CONFIG=%TEMP%\opamp-logstash.conf"
set "CONTAINER_NAME=opamp-logstash"
set "CONTAINER_CONFIG=/usr/share/logstash/pipeline/logstash.conf"
set "CONTAINER_OUT=/usr/share/logstash/out"
set "CONTAINER_RUNTIME=docker"
set "RUNTIME_REPLACE_ARG="

if not "%~1"=="" (
    if /i "%~1"=="podman" (
        set "CONTAINER_RUNTIME=podman"
        set "RUNTIME_REPLACE_ARG=--replace"
    ) else if /i "%~1"=="docker" (
        set "CONTAINER_RUNTIME=docker"
    ) else (
        echo Usage: %~nx0 [docker^|podman]
        exit /b 1
    )
)

if not exist "%CONFIG_FILE%" (
    echo Missing Logstash config: "%CONFIG_FILE%"
    exit /b 1
)

where "%CONTAINER_RUNTIME%" >nul 2>nul
if errorlevel 1 (
    echo Container runtime not found: %CONTAINER_RUNTIME%
    exit /b 1
)

if not exist "%OUT_DIR%" (
    mkdir "%OUT_DIR%" || exit /b 1
)

if not defined LOGSTASH_IMAGE (
    set "LOGSTASH_IMAGE=docker.elastic.co/logstash/logstash:9.5.1"
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$config = Get-Content -Raw -LiteralPath $env:CONFIG_FILE; " ^
    "$config = $config -replace [regex]::Escape('D:/dev/opamp/tests/logstash/out'), $env:CONTAINER_OUT; " ^
    "$config = $config -replace [regex]::Escape('D:\dev\opamp\tests\logstash\out'), $env:CONTAINER_OUT; " ^
    "$utf8 = New-Object System.Text.UTF8Encoding($false); " ^
    "[System.IO.File]::WriteAllText($env:TEMP_CONFIG, $config, $utf8)"

if errorlevel 1 (
    echo Failed to prepare container Logstash config.
    exit /b 1
)

echo Using image: %LOGSTASH_IMAGE%
echo Using runtime: %CONTAINER_RUNTIME%
echo Using config: %CONFIG_FILE%
echo Writing output under: %OUT_DIR%
echo.

"%CONTAINER_RUNTIME%" run --rm ^
    !RUNTIME_REPLACE_ARG! ^
    --name "%CONTAINER_NAME%" ^
    -p 127.0.0.1:5044:5044 ^
    -v "%TEMP_CONFIG%:%CONTAINER_CONFIG%:ro" ^
    -v "%OUT_DIR%:%CONTAINER_OUT%" ^
    "%LOGSTASH_IMAGE%" ^
    logstash -f "%CONTAINER_CONFIG%" --path.logs "%CONTAINER_OUT%/logs"

exit /b %ERRORLEVEL%
