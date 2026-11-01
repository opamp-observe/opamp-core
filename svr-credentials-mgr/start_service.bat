@echo off
REM Copyright 2026 opamp.info
REM Licensed under the Apache License, Version 2.0 (the "License");
REM you may not use this file except in compliance with the License.
REM You may obtain a copy of the License at
REM http://www.apache.org/licenses/LICENSE-2.0
REM Unless required by applicable law or agreed to in writing, software
REM distributed under the License is distributed on an "AS IS" BASIS,
REM WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
REM See the License for the specific language governing permissions and
REM limitations under the License.

setlocal

REM Resolve all paths relative to this script so it works from any directory.
set "SERVICE_ROOT=%~dp0"
set "VENV_ROOT=%SERVICE_ROOT%.venv"
set "VENV_PYTHON=%VENV_ROOT%\Scripts\python.exe"
set "DATA_ROOT=%SERVICE_ROOT%data"

REM Create and populate the development environment only when it is absent.
if not exist "%VENV_PYTHON%" (
    echo Creating the Python virtual environment...
    py -3 -m venv "%VENV_ROOT%"
    if errorlevel 1 goto :error

    echo Installing the server credentials manager...
    "%VENV_PYTHON%" -m pip install -e "%SERVICE_ROOT%[dev]"
    if errorlevel 1 goto :error
)

if not exist "%DATA_ROOT%" mkdir "%DATA_ROOT%"
if errorlevel 1 goto :error

REM Respect caller-provided values and otherwise select plaintext local files.
if not defined SVR_CREDENTIALS_KEYRING_BACKEND set "SVR_CREDENTIALS_KEYRING_BACKEND=plaintext"
if not defined SVR_CREDENTIALS_PLAINTEXT_PATH set "SVR_CREDENTIALS_PLAINTEXT_PATH=%DATA_ROOT%\credentials.json"
if not defined SVR_CREDENTIALS_MAPPING_PATH set "SVR_CREDENTIALS_MAPPING_PATH=%DATA_ROOT%\client-mappings.json"
if not defined SVR_CREDENTIALS_FILE_DIRECTORY set "SVR_CREDENTIALS_FILE_DIRECTORY=%DATA_ROOT%\connection-files"

echo Starting the server credentials manager...
echo Default UI: http://127.0.0.1:8091/svr-credentials-manager-service/ui
"%VENV_PYTHON%" -m svr_credentials_manager_service %*
if errorlevel 1 goto :error

endlocal
exit /b 0

:error
echo Server credentials manager failed with exit code %errorlevel%.
endlocal
exit /b 1
