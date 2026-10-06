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
    [string]$OutputDirectory = "",
    [string]$ArchivePath = ""
)

# Build the deployable payload on the operator workstation. The resulting tar
# archive is consumed by Linux EC2 user data, so text portability is enforced here.
$ErrorActionPreference = "Stop"
$utf8NoBomEncoding = New-Object System.Text.UTF8Encoding -ArgumentList $false

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $RepoRoot "dist\cloud-aws-artifacts"
}
if (-not $ArchivePath) {
    $ArchivePath = Join-Path $RepoRoot "dist\opamp-cloud-artifacts.tar.gz"
}

$resolvedRepoRoot = [IO.Path]::GetFullPath($RepoRoot)
$resolvedOutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
# Constrain recursive cleanup to the repository's generated dist directory.
$expectedOutputPrefix = [IO.Path]::GetFullPath((Join-Path $resolvedRepoRoot "dist")) + [IO.Path]::DirectorySeparatorChar
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
if (Test-Path -LiteralPath $ArchivePath) {
    Remove-Item -LiteralPath $ArchivePath -Force
}
New-Item -ItemType Directory -Path $wheelDirectory, $scriptDirectory -Force | Out-Null

# Build each independently packaged component into one wheel directory. VMs
# install role-specific subsets from this common artifact.
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
    # Normalize Linux scripts because Windows checkouts may otherwise package CRLF files.
    $runtimeScriptContent = [IO.File]::ReadAllText($runtimeScriptSource).Replace("`r`n", "`n")
    [IO.File]::WriteAllText(
        $runtimeScriptDestination,
        $runtimeScriptContent,
        $utf8NoBomEncoding
    )
}
# The manifest avoids guessing wheel filenames on the VM and preserves a stable,
# inspectable contract between packaging and installation.
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

$archiveReadme = @"
This archive contains the OpAMP wheels and platform-neutral VM bootstrap scripts
used by cloud/aws/template.yaml. Upload the generated tar.gz file to the private
S3 bucket and object key supplied to cloud/aws/deploy.sh or deploy.ps1.
"@
[IO.File]::WriteAllText(
    (Join-Path $resolvedOutputDirectory "README.txt"),
    $archiveReadme,
    $utf8NoBomEncoding
)

# CloudFormation passes one S3 object to each VM, so wrap wheels and scripts in
# a single gzip-compressed tar archive.
& tar -czf $ArchivePath -C $resolvedOutputDirectory .
if ($LASTEXITCODE -ne 0) {
    throw "Unable to create $ArchivePath."
}
Write-Output "Packaged AWS artifacts in $ArchivePath"
