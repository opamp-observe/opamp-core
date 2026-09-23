@echo off
setlocal

where powershell >nul 2>&1
if not %errorlevel%==0 (
  echo PowerShell is required to terminate Smart Log Viewer and verify ports.
  exit /b 1
)

set "TEMP_PS1=%TEMP%\opamp_stop_slv_%RANDOM%%RANDOM%.ps1"

> "%TEMP_PS1%" echo $ErrorActionPreference = 'SilentlyContinue'
>> "%TEMP_PS1%" echo $allProcesses = @(Get-CimInstance Win32_Process)
>> "%TEMP_PS1%" echo $processById = @{}
>> "%TEMP_PS1%" echo foreach ($process in $allProcesses) { $processById[[int]$process.ProcessId] = $process }
>> "%TEMP_PS1%" echo $excludedIds = New-Object 'System.Collections.Generic.HashSet[int]'
>> "%TEMP_PS1%" echo $current = $processById[[int]$PID]
>> "%TEMP_PS1%" echo while ($current) {
>> "%TEMP_PS1%" echo   [void]$excludedIds.Add([int]$current.ProcessId)
>> "%TEMP_PS1%" echo   $parentId = [int]$current.ParentProcessId
>> "%TEMP_PS1%" echo   if ($parentId -le 0 -or -not $processById.ContainsKey($parentId)) { break }
>> "%TEMP_PS1%" echo   $current = $processById[$parentId]
>> "%TEMP_PS1%" echo }
>> "%TEMP_PS1%" echo function Test-SmartLogViewerProcess($process) {
>> "%TEMP_PS1%" echo   $name = [string]$process.Name
>> "%TEMP_PS1%" echo   $commandLine = [string]$process.CommandLine
>> "%TEMP_PS1%" echo   $nameLower = $name.ToLowerInvariant()
>> "%TEMP_PS1%" echo   $commandLower = $commandLine.ToLowerInvariant()
>> "%TEMP_PS1%" echo   if ($commandLower.Contains('terminate_smart_log_viewer') -or $commandLower.Contains('terminate-smart-log-viewer')) { return $false }
>> "%TEMP_PS1%" echo   if ($nameLower -eq 'smart-log-viewer.exe' -or $nameLower -eq 'smart-log-viewer.cmd') { return $true }
>> "%TEMP_PS1%" echo   if ($commandLower.Contains('smart-log-viewer') -or $commandLower.Contains('smart-log-vieewer')) { return $true }
>> "%TEMP_PS1%" echo   return $false
>> "%TEMP_PS1%" echo }
>> "%TEMP_PS1%" echo $rootIds = @($allProcesses ^| Where-Object { -not $excludedIds.Contains([int]$_.ProcessId) -and (Test-SmartLogViewerProcess $_) } ^| ForEach-Object { [int]$_.ProcessId } ^| Sort-Object -Unique)
>> "%TEMP_PS1%" echo if ($rootIds.Count -eq 0) {
>> "%TEMP_PS1%" echo   Write-Host 'No Smart Log Viewer process found.'
>> "%TEMP_PS1%" echo   exit 0
>> "%TEMP_PS1%" echo }
>> "%TEMP_PS1%" echo $targetSet = New-Object 'System.Collections.Generic.HashSet[int]'
>> "%TEMP_PS1%" echo foreach ($processId in $rootIds) { [void]$targetSet.Add([int]$processId) }
>> "%TEMP_PS1%" echo $changed = $true
>> "%TEMP_PS1%" echo while ($changed) {
>> "%TEMP_PS1%" echo   $changed = $false
>> "%TEMP_PS1%" echo   foreach ($process in $allProcesses) {
>> "%TEMP_PS1%" echo     $processId = [int]$process.ProcessId
>> "%TEMP_PS1%" echo     $parentId = [int]$process.ParentProcessId
>> "%TEMP_PS1%" echo     if (-not $targetSet.Contains($processId) -and $targetSet.Contains($parentId)) {
>> "%TEMP_PS1%" echo       [void]$targetSet.Add($processId)
>> "%TEMP_PS1%" echo       $changed = $true
>> "%TEMP_PS1%" echo     }
>> "%TEMP_PS1%" echo   }
>> "%TEMP_PS1%" echo }
>> "%TEMP_PS1%" echo $targetIds = @($targetSet ^| Sort-Object -Unique)
>> "%TEMP_PS1%" echo $connections = @(Get-NetTCPConnection ^| Where-Object { $targetSet.Contains([int]$_.OwningProcess) })
>> "%TEMP_PS1%" echo $ports = @($connections ^| Where-Object { $_.LocalPort } ^| ForEach-Object { [int]$_.LocalPort } ^| Sort-Object -Unique)
>> "%TEMP_PS1%" echo Write-Host ('Stopping Smart Log Viewer process id(s): ' + ($targetIds -join ', '))
>> "%TEMP_PS1%" echo if ($ports.Count -gt 0) { Write-Host ('Observed Smart Log Viewer TCP port(s): ' + ($ports -join ', ')) }
>> "%TEMP_PS1%" echo foreach ($processId in ($targetIds ^| Sort-Object -Descending)) {
>> "%TEMP_PS1%" echo   Stop-Process -Id $processId -Force
>> "%TEMP_PS1%" echo }
>> "%TEMP_PS1%" echo Start-Sleep -Milliseconds 1000
>> "%TEMP_PS1%" echo $stillRunning = @($targetIds ^| Where-Object { Get-Process -Id $_ })
>> "%TEMP_PS1%" echo if ($stillRunning.Count -gt 0) {
>> "%TEMP_PS1%" echo   foreach ($processId in $stillRunning) { taskkill /PID $processId /T /F ^| Out-Null }
>> "%TEMP_PS1%" echo   Start-Sleep -Milliseconds 1000
>> "%TEMP_PS1%" echo }
>> "%TEMP_PS1%" echo if ($ports.Count -gt 0) {
>> "%TEMP_PS1%" echo   $remaining = @(Get-NetTCPConnection ^| Where-Object { $ports -contains [int]$_.LocalPort })
>> "%TEMP_PS1%" echo   if ($remaining.Count -gt 0) {
>> "%TEMP_PS1%" echo     $details = @($remaining ^| ForEach-Object { ('port ' + $_.LocalPort + ' pid ' + $_.OwningProcess + ' state ' + $_.State) } ^| Sort-Object -Unique)
>> "%TEMP_PS1%" echo     Write-Host ('Warning: Smart Log Viewer TCP port(s) still open: ' + ($details -join '; '))
>> "%TEMP_PS1%" echo     exit 1
>> "%TEMP_PS1%" echo   }
>> "%TEMP_PS1%" echo }
>> "%TEMP_PS1%" echo Write-Host 'Smart Log Viewer terminated and observed TCP ports are closed.'

powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS1%"
set "EXIT_CODE=%errorlevel%"
del "%TEMP_PS1%" >nul 2>&1
exit /b %EXIT_CODE%
