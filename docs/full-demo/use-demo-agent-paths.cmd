@echo off
rem Licensed under the Apache License, Version 2.0.
rem Copyright 2026 mp3monster.org
rem
rem Prepend the default local demo agent folders to PATH for this shell.
rem Usage from cmd.exe:
rem   call docs\full-demo\use-demo-agent-paths.cmd

set "VECTOR_HOME=D:\dev-tools\vector\bin"
set "ELASTIC_AGENT_HOME=D:\dev-tools\elastic-agent\elastic-agent-9.5.0-windows-x86_64"
set "HEARTBEAT_HOME=D:\dev-tools\elastic-heartbeat\heartbeat-9.5.3-windows-x86_64"

set "PATH=%VECTOR_HOME%;%ELASTIC_AGENT_HOME%;%HEARTBEAT_HOME%;%PATH%"

echo Demo agent paths prepended to PATH:
echo   %VECTOR_HOME%
echo   %ELASTIC_AGENT_HOME%
echo   %HEARTBEAT_HOME%
echo.
echo You can now run:
echo   vector --version
echo   elastic-agent version
echo   heartbeat version
