# Copyright 2026 mp3monster.org
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

param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path,
    [string]$OutputDirectory = ""
)

# Build the directory uploaded to Azure Blob Storage. Linux VM extensions read
# its wheel manifest and runtime scripts directly over HTTPS.
$ErrorActionPreference = "Stop"
$utf8NoBomEncoding = New-Object System.Text.UTF8Encoding -ArgumentList $false

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $RepoRoot "dist\cloud-azure-artifacts"
}

$resolvedRepoRoot = [IO.Path]::GetFullPath($RepoRoot)
$resolvedOutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
# Constrain recursive cleanup to generated content under the repository's dist directory.
$expectedOutputPrefix = [IO.Path]::GetFullPath((Join-Path $resolvedRepoRoot "dist")) +
    [IO.Path]::DirectorySeparatorChar
if (-not $resolvedOutputDirectory.StartsWith($expectedOutputPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDirectory must be inside $expectedOutputPrefix"
}

$componentPaths = @(
    "provider",
    "consumer",
    "consumer-sim",
    "config-service",
    "client-config-generator-service",
    "catalog-service",
    "cli",
    "agent_broker",
    "mcp",
    "svr-credentials-mgr/plaintext-keyring",
    "svr-credentials-mgr",
    "dev-tools"
)
$runtimeScripts = @(
    "install-opamp.sh",
    "start-opamp-consumer.sh",
    "start-opamp-server.sh",
    "upgrade-opamp-wheels.sh"
)
$pythonCommand = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
$wheelDirectory = Join-Path $resolvedOutputDirectory "wheels"
$scriptDirectory = Join-Path $resolvedOutputDirectory "scripts"

if (Test-Path -LiteralPath $resolvedOutputDirectory) {
    Remove-Item -LiteralPath $resolvedOutputDirectory -Recurse -Force
}
New-Item -ItemType Directory -Path $wheelDirectory, $scriptDirectory -Force | Out-Null

# Build every deployable Python component once; each VM installs only its role's subset.
& $pythonCommand -m pip install --upgrade build
if ($LASTEXITCODE -ne 0) {
    throw "Unable to install the Python build package."
}
foreach ($componentPath in $componentPaths) {
    & $pythonCommand -m build --wheel --outdir $wheelDirectory (Join-Path $resolvedRepoRoot $componentPath)
    if ($LASTEXITCODE -ne 0) {
        throw "Wheel build failed for $componentPath."
    }
}

foreach ($runtimeScript in $runtimeScripts) {
    $runtimeScriptSource = Join-Path $resolvedRepoRoot "cloud\azure\scripts\$runtimeScript"
    $runtimeScriptDestination = Join-Path $scriptDirectory $runtimeScript
    # Normalize Linux scripts because Windows checkouts may otherwise upload CRLF files.
    $runtimeScriptContent = [IO.File]::ReadAllText($runtimeScriptSource).Replace("`r`n", "`n")
    [IO.File]::WriteAllText(
        $runtimeScriptDestination,
        $runtimeScriptContent,
        $utf8NoBomEncoding
    )
}
# The wheel manifest is the stable handoff from workstation packaging to VM installation.
$wheelNames = Get-ChildItem -LiteralPath $wheelDirectory -Filter "*.whl" -File |
    Sort-Object Name |
    Select-Object -ExpandProperty Name
$wheelManifestContent = [string]::Join("`n", [string[]]$wheelNames) + "`n"
# Write a Linux-readable manifest because each entry becomes a shell path on the VM.
[IO.File]::WriteAllText(
    (Join-Path $wheelDirectory "wheels.txt"),
    $wheelManifestContent,
    $utf8NoBomEncoding
)

$artifactReadme = @"
This directory contains the OpAMP wheels and VM bootstrap scripts uploaded by
cloud/azure/deploy.ps1 to its retained Azure artifact container.
"@
[IO.File]::WriteAllText(
    (Join-Path $resolvedOutputDirectory "README.txt"),
    $artifactReadme,
    $utf8NoBomEncoding
)

Write-Output "Packaged Azure artifacts in $resolvedOutputDirectory"
