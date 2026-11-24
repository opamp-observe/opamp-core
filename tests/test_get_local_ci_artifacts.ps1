# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/get_local_ci_artifacts.ps1'
$global:mockArguments = @()
$global:mockExitCode = 0

# Capture a GitHub CLI artifact download. Arguments are CLI tokens.
function global:gh {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $global:mockArguments = @($Arguments)
    $global:LASTEXITCODE = $global:mockExitCode
}

try {
    & $scriptPath -RunId 12345 -Destination 'D:\reports' | Out-Null
    if ($global:mockArguments[0] -ne 'run' -or $global:mockArguments[1] -ne 'download' -or
        $global:mockArguments -notcontains 'opamp-observe/opamp-private-ci' -or
        $global:mockArguments -notcontains 'opamp-regression-*' -or
        $global:mockArguments -notcontains 'D:\reports') {
        throw 'Artifact download used the wrong repository, pattern, or destination.'
    }

    $global:mockExitCode = 1
    try {
        & $scriptPath -RunId 12345 -Destination 'D:\reports' | Out-Null
        throw 'A failed download was reported as success.'
    } catch {
        if ($_.Exception.Message -eq 'A failed download was reported as success.') { throw }
    }
    Write-Output 'PASS: private CI artifact download checks'
} finally {
    Remove-Item Function:gh -ErrorAction SilentlyContinue
    Remove-Variable mockArguments, mockExitCode -Scope Global -ErrorAction SilentlyContinue
}
