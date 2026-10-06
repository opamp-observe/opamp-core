# Licensed under the Apache License, Version 2.0.
# Copyright 2026 mp3monster.org

[CmdletBinding()]
param(
    [string]$VectorExe = "vector",
    [string]$ElasticAgentExe = "elastic-agent",
    [string]$HeartbeatExe = "heartbeat",
    [string]$LogstashHost = "127.0.0.1",
    [string]$PidFile = "docs\full-demo\out\observed-agent-pids.json"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$outPath = Join-Path $repoRoot $PidFile
$outDir = Split-Path -Parent $outPath
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$processes = @()

function Join-OptionalPath {
    param(
        [string]$BasePath,
        [string]$ChildPath
    )

    if ([string]::IsNullOrWhiteSpace($BasePath)) {
        return $null
    }
    return Join-Path $BasePath $ChildPath
}

# Vector resolution order:
# 1. -VectorExe when supplied as a path or PATH command.
# 2. OPAMP_VECTOR_EXECUTABLE_PATH or OPAMP_VECTOR_EXE.
# 3. OPAMP_VECTOR_HOME joined with vector.exe.
# 4. PATH command lookup.
# 5. The editable candidate list below.
$VectorCandidatePaths = @(
    (Join-Path $repoRoot "tools\vector\bin\vector.exe"),
    (Join-Path $repoRoot "dev-tools\vector\bin\vector.exe"),
    "D:\dev-tools\vector\bin\vector.exe",
    (Join-OptionalPath $env:ProgramFiles "Vector\bin\vector.exe"),
    (Join-OptionalPath $env:ProgramFiles "Vector\vector.exe"),
    (Join-OptionalPath $env:LOCALAPPDATA "Programs\Vector\bin\vector.exe"),
    (Join-OptionalPath $env:LOCALAPPDATA "Programs\Vector\vector.exe")
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

function Resolve-AgentExecutable {
    param(
        [string]$Name,
        [string]$FilePath
    )

    if (Test-Path -LiteralPath $FilePath -PathType Leaf) {
        return (Resolve-Path -LiteralPath $FilePath).Path
    }

    $command = Get-Command $FilePath -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw "$Name executable not found as a file path or PATH command: $FilePath"
}

function Resolve-VectorExecutable {
    param(
        [string]$FilePath,
        [string[]]$CandidatePaths
    )

    $explicitValue = -not [string]::IsNullOrWhiteSpace($FilePath) -and $FilePath -ne "vector"
    if ($explicitValue) {
        return Resolve-AgentExecutable -Name "Vector" -FilePath $FilePath
    }

    $environmentCandidates = @(
        $env:OPAMP_VECTOR_EXECUTABLE_PATH,
        $env:OPAMP_VECTOR_EXE
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    foreach ($candidate in $environmentCandidates) {
        try {
            return Resolve-AgentExecutable -Name "Vector" -FilePath $candidate
        } catch {
            Write-Verbose "Vector candidate failed: $candidate"
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($env:OPAMP_VECTOR_HOME)) {
        $homeCandidate = Join-Path $env:OPAMP_VECTOR_HOME "vector.exe"
        try {
            return Resolve-AgentExecutable -Name "Vector" -FilePath $homeCandidate
        } catch {
            Write-Verbose "Vector home candidate failed: $homeCandidate"
        }
    }

    $pathCommand = Get-Command "vector" -ErrorAction SilentlyContinue
    if ($pathCommand) {
        return $pathCommand.Source
    }

    foreach ($candidate in $CandidatePaths) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $candidateText = ($CandidatePaths -join "`n  ")
    throw "Vector executable not found. Set -VectorExe, OPAMP_VECTOR_EXECUTABLE_PATH, OPAMP_VECTOR_EXE, OPAMP_VECTOR_HOME, PATH, or edit `$VectorCandidatePaths in this script. Checked:`n  $candidateText"
}

function Start-ObservedAgent {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    $executable = Resolve-AgentExecutable -Name $Name -FilePath $FilePath
    if (-not (Test-Path -LiteralPath $WorkingDirectory)) {
        throw "$Name working directory not found: $WorkingDirectory"
    }

    $process = Start-Process `
        -FilePath $executable `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -PassThru `
        -WindowStyle Hidden
    $script:processes += [ordered]@{
        name = $Name
        pid = $process.Id
        executable = $executable
        working_directory = $WorkingDirectory
        arguments = $ArgumentList
    }
    Write-Host "Started $Name pid=$($process.Id)"
}

$env:OPAMP_LOGSTASH_HOST = $LogstashHost
$env:OPAMP_FULL_DEMO_OUT = (Join-Path $repoRoot "docs\full-demo\out")

$resolvedVectorExe = Resolve-VectorExecutable `
    -FilePath $VectorExe `
    -CandidatePaths $VectorCandidatePaths

Start-ObservedAgent `
    -Name "Vector" `
    -FilePath $resolvedVectorExe `
    -ArgumentList @("--config", (Join-Path $repoRoot "docs\full-demo\active\vector.yaml")) `
    -WorkingDirectory $repoRoot

Start-ObservedAgent `
    -Name "Elastic Agent" `
    -FilePath $ElasticAgentExe `
    -ArgumentList @("run", "-c", (Join-Path $repoRoot "docs\full-demo\active\elastic-agent.yml")) `
    -WorkingDirectory $repoRoot

Start-ObservedAgent `
    -Name "Elastic Heartbeat" `
    -FilePath $HeartbeatExe `
    -ArgumentList @("-e", "-c", (Join-Path $repoRoot "docs\full-demo\active\heartbeat.yml")) `
    -WorkingDirectory $repoRoot

$processes | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $outPath -Encoding UTF8
Write-Host "PID file: $outPath"
