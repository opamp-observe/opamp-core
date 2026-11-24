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
$scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/run_local_ci.ps1'
$reviewedSha = '72d35d1717d0d8db24bf8357be52182a3badcd28'
$global:mockCalls = @()
$global:mockApiSha = $reviewedSha

# Replace gh for this test process and capture its arguments. Arguments are CLI tokens.
function global:gh {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $global:mockCalls += ,@($Arguments)
    $global:LASTEXITCODE = 0
    if ($Arguments[0] -eq 'api') { return $global:mockApiSha }
}

try {
    & $scriptPath -ReviewedSha $reviewedSha | Out-Null
    if ($global:mockCalls.Count -ne 2) { throw 'Expected SHA lookup and one dispatch.' }
    if ($global:mockCalls[0][1] -ne "repos/opamp-observe/opamp-core/commits/$reviewedSha") {
        throw 'Commit lookup used the wrong source repository.'
    }
    if ($global:mockCalls[1][0] -ne 'workflow' -or $global:mockCalls[1][1] -ne 'run') {
        throw 'Expected a GitHub workflow dispatch.'
    }
    if ($global:mockCalls[1] -notcontains "source_sha=$reviewedSha") {
        throw 'The reviewed SHA was not dispatched.'
    }
    if ($global:mockCalls[1] -notcontains 'test_suite=all') {
        throw 'The complete suite was not the dispatch default.'
    }

    $global:mockCalls = @()
    & $scriptPath -ReviewedSha $reviewedSha -TestSuite regression-pack -RegressionTestId st001 | Out-Null
    if ($global:mockCalls[1] -notcontains 'test_suite=regression-pack' -or
        $global:mockCalls[1] -notcontains 'regression_test_id=st001') {
        throw 'Selected regression scenario was not dispatched.'
    }

    $global:mockCalls = @()
    try {
        & $scriptPath -ReviewedSha $reviewedSha -TestSuite syntax -RegressionTestId st001 | Out-Null
        throw 'Scenario was accepted for syntax-only mode.'
    } catch {
        if ($_.Exception.Message -eq 'Scenario was accepted for syntax-only mode.') { throw }
    }
    if ($global:mockCalls.Count -ne 0) { throw 'Invalid test selection reached GitHub.' }

    $global:mockCalls = @()
    $global:mockApiSha = '0000000000000000000000000000000000000000'
    try {
        & $scriptPath -ReviewedSha $reviewedSha | Out-Null
        throw 'A mismatched API SHA was accepted.'
    } catch {
        if ($_.Exception.Message -eq 'A mismatched API SHA was accepted.') { throw }
    }
    if ($global:mockCalls.Count -ne 1) { throw 'A mismatched SHA caused a dispatch.' }

    $global:mockCalls = @()
    try {
        & $scriptPath -ReviewedSha deadbeef | Out-Null
        throw 'A short SHA was accepted.'
    } catch {
        if ($_.Exception.Message -eq 'A short SHA was accepted.') { throw }
    }
    if ($global:mockCalls.Count -ne 0) { throw 'An invalid SHA reached GitHub.' }
    Write-Output 'PASS: local CI dispatch argument checks'
} finally {
    Remove-Item Function:gh -ErrorAction SilentlyContinue
    Remove-Variable mockCalls, mockApiSha -Scope Global -ErrorAction SilentlyContinue
}
