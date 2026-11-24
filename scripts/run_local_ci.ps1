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

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ReviewedSha,
    [ValidatePattern('^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')]
    [string]$SourceRepository = 'opamp-observe/opamp-core'
)

$ErrorActionPreference = 'Stop'
$DebugPreference = 'Continue'
$privateCiRepository = 'opamp-observe/opamp-private-ci'
$workflowName = 'manual-build.yml'
$resolvedSha = & gh api "repos/$SourceRepository/commits/$ReviewedSha" --jq .sha
if ($LASTEXITCODE -ne 0 -or $resolvedSha -ne $ReviewedSha.ToLowerInvariant()) {
    throw "Commit $ReviewedSha could not be verified in $SourceRepository."
}

& gh workflow run $workflowName --repo $privateCiRepository --ref main `
    --field "source_repository=$SourceRepository" --field "source_sha=$ReviewedSha"
if ($LASTEXITCODE -ne 0) {
    throw 'The private CI workflow dispatch failed.'
}
Write-Output "Dispatched reviewed commit $ReviewedSha to $privateCiRepository."
