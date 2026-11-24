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
    [ValidateRange(1, [long]::MaxValue)]
    [long]$RunId,
    [string]$Destination
)

$ErrorActionPreference = 'Stop'
$DebugPreference = 'Continue'
$privateCiRepository = 'opamp-observe/opamp-private-ci'
$artifactPattern = 'opamp-regression-*'
if ([string]::IsNullOrWhiteSpace($Destination)) {
    $repositoryRoot = Split-Path -Parent $PSScriptRoot
    $Destination = Join-Path $repositoryRoot "dist/local-ci-artifacts/$RunId"
}

& gh run download $RunId --repo $privateCiRepository --dir $Destination --pattern $artifactPattern
if ($LASTEXITCODE -ne 0) {
    throw "Could not download artifacts for private CI run $RunId."
}
Write-Output "Downloaded private CI run $RunId artifacts to $Destination."
