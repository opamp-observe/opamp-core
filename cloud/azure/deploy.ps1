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
    [string]$ResourceGroup = "opamp-regression-rg",
    [string]$RetentionResourceGroup = "",
    [string]$Location = "uksouth",
    [string]$ParametersFile = "cloud/azure/parameters.example.json",
    [string]$TemplateFile = "cloud/azure/mainTemplate.json",
    [string]$StorageAccount = "",
    [string]$ArtifactContainer = "opamp-cloud",
    [string]$ResultsContainer = "opamp-regression-results",
    [string]$ArtifactDirectory = "dist/cloud-azure-artifacts",
    [string]$StorageAccountFile = "dist/azure-retention-storage-account.txt",
    [string]$SshPrivateKeyFile = "",
    [switch]$SkipPackage
)

# Orchestrate the Azure deployment from the operator workstation. ARM owns the
# VM resource group; this script owns packaging, retained storage, and evidence.
$ErrorActionPreference = "Stop"
$deploymentTimestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmss")
$resultSetTimestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd-HH-mm-ss")
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$utf8NoBomEncoding = New-Object System.Text.UTF8Encoding -ArgumentList $false

# Phase 1: make all relative paths repository-relative and validate prerequisites.
if (-not [IO.Path]::IsPathRooted($ParametersFile)) {
    $ParametersFile = Join-Path $repositoryRoot $ParametersFile
}
if (-not [IO.Path]::IsPathRooted($TemplateFile)) {
    $TemplateFile = Join-Path $repositoryRoot $TemplateFile
}
if (-not [IO.Path]::IsPathRooted($ArtifactDirectory)) {
    $ArtifactDirectory = Join-Path $repositoryRoot $ArtifactDirectory
}
if (-not [IO.Path]::IsPathRooted($StorageAccountFile)) {
    $StorageAccountFile = Join-Path $repositoryRoot $StorageAccountFile
}
if ($SshPrivateKeyFile -and -not [IO.Path]::IsPathRooted($SshPrivateKeyFile)) {
    $SshPrivateKeyFile = Join-Path $repositoryRoot $SshPrivateKeyFile
}

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required."
}
$pythonCommand = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
$pythonArguments = if ($pythonCommand -eq "py") { @("-3") } else { @() }
if (-not (Test-Path -LiteralPath $ParametersFile)) {
    throw "Parameter file not found: $ParametersFile"
}

# Phase 2: build the wheels and platform-neutral VM scripts unless a previously
# inspected artifact directory was explicitly requested.
if (-not $SkipPackage) {
    & (Join-Path $PSScriptRoot "scripts\package-cloud-artifacts.ps1") `
        -OutputDirectory $ArtifactDirectory
}
if (-not (Test-Path -LiteralPath $ArtifactDirectory -PathType Container)) {
    throw "Artifact directory not found: $ArtifactDirectory"
}

# Phase 3: keep storage in a separate resource group so deleting the VM resource
# group preserves deployment artifacts and timestamped regression evidence.
if (-not $StorageAccount) {
    $subscriptionId = (& az account show --query id --output tsv | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $subscriptionId) {
        throw "Unable to determine the Azure subscription ID."
    }
    $subscriptionSuffix = ($subscriptionId -replace "-", "").Substring(0, 5).ToLowerInvariant()
    $StorageAccount = "opamp$deploymentTimestamp$subscriptionSuffix"
    if (-not $RetentionResourceGroup) {
        $RetentionResourceGroup = "$ResourceGroup-retained"
    }
    if ($RetentionResourceGroup -eq $ResourceGroup) {
        throw "RetentionResourceGroup must differ from ResourceGroup."
    }
    & az group create --name $RetentionResourceGroup --location $Location | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create retained resource group $RetentionResourceGroup."
    }
    & az storage account create `
        --resource-group $RetentionResourceGroup `
        --name $StorageAccount `
        --location $Location `
        --sku Standard_LRS `
        --kind StorageV2 `
        --min-tls-version TLS1_2 `
        --https-only true `
        --allow-blob-public-access true `
        --tags Project=opamp Purpose=regression-retention CreatedAt=$deploymentTimestamp | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create retained Azure storage account $StorageAccount."
    }
    Write-Output "Created retained Azure storage account $StorageAccount"
} else {
    $storageResourceGroup = (& az storage account show `
        --name $StorageAccount `
        --query resourceGroup `
        --output tsv | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $storageResourceGroup) {
        throw "Unable to find retained Azure storage account $StorageAccount."
    }
    if ($storageResourceGroup -eq $ResourceGroup) {
        throw "Storage account $StorageAccount is inside deployment resource group $ResourceGroup."
    }
    Write-Output "Using retained Azure storage account $StorageAccount"
}

$storageAccountDirectory = Split-Path -Parent $StorageAccountFile
if ($storageAccountDirectory) {
    New-Item -ItemType Directory -Path $storageAccountDirectory -Force | Out-Null
}
[IO.File]::WriteAllText(
    $StorageAccountFile,
    "$StorageAccount`r`n",
    $utf8NoBomEncoding
)

# The public artifact container is read by VM extensions during bootstrap. The
# results container is private because it stores operational deployment output.
& az storage container create `
    --account-name $StorageAccount `
    --name $ArtifactContainer `
    --public-access blob `
    --auth-mode key | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Unable to create artifact container $ArtifactContainer."
}
& az storage container create `
    --account-name $StorageAccount `
    --name $ResultsContainer `
    --public-access off `
    --auth-mode key | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Unable to create results container $ResultsContainer."
}
& az storage blob upload-batch `
    --account-name $StorageAccount `
    --destination $ArtifactContainer `
    --source $ArtifactDirectory `
    --auth-mode key `
    --overwrite | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Unable to upload Azure deployment artifacts."
}

$artifactBaseUrl = "https://$StorageAccount.blob.core.windows.net/$ArtifactContainer"
$resultsDirectory = Join-Path $repositoryRoot "dist/azure-regression-results/$resultSetTimestamp"
$connectionGuideFile = Join-Path $resultsDirectory "connection_details.md"
$deploymentOutputsFile = Join-Path $resultsDirectory "deployment-outputs.json"
New-Item -ItemType Directory -Path $resultsDirectory -Force | Out-Null

# Phase 4: ARM creates or updates networking and VMs. Custom Script Extensions
# download the uploaded artifacts and report bootstrap status to ARM.
& az group create --name $ResourceGroup --location $Location | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Unable to create deployment resource group $ResourceGroup."
}
$deploymentOutputs = & az deployment group create `
    --resource-group $ResourceGroup `
    --template-file $TemplateFile `
    --parameters "@$ParametersFile" `
    "artifactBaseUrl=$artifactBaseUrl" `
    "wheelArtifactBaseUrl=$artifactBaseUrl" `
    --query properties.outputs `
    --output json
if ($LASTEXITCODE -ne 0) {
    throw "Azure deployment failed."
}
[IO.File]::WriteAllLines(
    $deploymentOutputsFile,
    [string[]]$deploymentOutputs,
    $utf8NoBomEncoding
)
# Phase 5: normalize ARM outputs into the common guide and retain both files.
$connectionGuideArguments = @(
    (Join-Path $repositoryRoot "scripts/generate_cloud_connection_guide.py"),
    "--provider", "azure",
    "--outputs-file", $deploymentOutputsFile,
    "--output-file", $connectionGuideFile
)
if ($SshPrivateKeyFile) {
    $connectionGuideArguments += @("--ssh-private-key", $SshPrivateKeyFile)
}
$pythonInvocationArguments = @($pythonArguments) + $connectionGuideArguments
& $pythonCommand @pythonInvocationArguments
if ($LASTEXITCODE -ne 0 -or
    -not (Test-Path -LiteralPath $connectionGuideFile -PathType Leaf) -or
    (Get-Item -LiteralPath $connectionGuideFile).Length -eq 0) {
    throw "Unable to generate the Azure connection guide."
}

& az storage blob upload `
    --account-name $StorageAccount `
    --container-name $ResultsContainer `
    --name "$resultSetTimestamp/deployment-outputs.json" `
    --file $deploymentOutputsFile `
    --auth-mode key `
    --overwrite | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Unable to upload retained Azure deployment results."
}
& az storage blob upload `
    --account-name $StorageAccount `
    --container-name $ResultsContainer `
    --name "$resultSetTimestamp/connection_details.md" `
    --file $connectionGuideFile `
    --auth-mode key `
    --overwrite | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Unable to upload the Azure connection guide."
}

Write-Output $deploymentOutputs
Write-Output "Retained storage account: $StorageAccount"
Write-Output "Retained deployment results: $ResultsContainer/$resultSetTimestamp/"
Write-Output "Connection guide: $connectionGuideFile"
