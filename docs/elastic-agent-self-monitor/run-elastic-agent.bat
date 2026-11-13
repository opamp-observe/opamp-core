@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%elastic-agent.yml"
set "OUT_DIR=%SCRIPT_DIR%out"
set "AGENT_LOG_DIR=%OUT_DIR%\elastic-agent-logs"

if not defined ELASTIC_AGENT_HOME (
    set "ELASTIC_AGENT_HOME=D:\dev-tools\elastic-agent\elastic-agent-9.5.0-windows-x86_64"
)

set "AGENT_EXE=%ELASTIC_AGENT_HOME%\elastic-agent.exe"

if not exist "%AGENT_EXE%" (
    echo Missing Elastic Agent executable: "%AGENT_EXE%"
    echo Set ELASTIC_AGENT_HOME to the Elastic Agent directory and rerun this script.
    exit /b 1
)

if not exist "%CONFIG_FILE%" (
    echo Missing Elastic Agent config: "%CONFIG_FILE%"
    exit /b 1
)

if not exist "%OUT_DIR%" (
    mkdir "%OUT_DIR%" || exit /b 1
)

if not exist "%AGENT_LOG_DIR%" (
    mkdir "%AGENT_LOG_DIR%" || exit /b 1
)

echo Using Elastic Agent: %AGENT_EXE%
echo Using config: %CONFIG_FILE%
if defined OPAMP_LOGSTASH_HOST (
    echo Sending self-monitoring logs and metrics to Logstash at %OPAMP_LOGSTASH_HOST%:5044
) else (
    echo Sending self-monitoring logs and metrics to Logstash at 127.0.0.1:5044
)
echo Agent file logs: %AGENT_LOG_DIR%
echo.
echo Start Logstash first with:
echo   "%SCRIPT_DIR%run-logstash.bat"
echo If localhost forwarding fails, run:
echo   call "%SCRIPT_DIR%set-podman-logstash-host.bat"
echo.

pushd "%ELASTIC_AGENT_HOME%" || exit /b 1
"%AGENT_EXE%" run -c "%CONFIG_FILE%"
set "EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %EXIT_CODE%
