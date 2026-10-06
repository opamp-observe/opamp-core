# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

[CmdletBinding()]
param(
    [string]$PidFile = "docs\full-demo\out\observed-agent-pids.json"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$pidPath = Join-Path $repoRoot $PidFile

if (-not (Test-Path -LiteralPath $pidPath)) {
    Write-Host "No observed-agent PID file found: $pidPath"
    exit 0
}

$entries = Get-Content -LiteralPath $pidPath -Raw | ConvertFrom-Json
foreach ($entry in @($entries)) {
    $pidValue = [int]$entry.pid
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Write-Host "Already stopped: $($entry.name) pid=$pidValue"
        continue
    }
    Stop-Process -Id $pidValue -ErrorAction SilentlyContinue
    Write-Host "Stopped $($entry.name) pid=$pidValue"
}

Remove-Item -LiteralPath $pidPath -Force
