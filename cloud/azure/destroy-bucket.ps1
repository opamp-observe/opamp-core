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
    [Alias("BucketName")]
    [string]$StorageAccount = "",
    [switch]$All
)

$ErrorActionPreference = "Stop"

function Remove-RetainedStorageAccount {
    param(
        [Parameter(Mandatory = $true)][string]$SelectedStorageAccount,
        [string]$SelectedResourceGroup = ""
    )

    # Resolve the owning resource group before deletion because Azure storage
    # account names are globally unique but deletion is scoped to a group.
    if (-not $SelectedResourceGroup) {
        $SelectedResourceGroup = (& az storage account show `
            --name $SelectedStorageAccount `
            --query resourceGroup `
            --output tsv | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $SelectedResourceGroup) {
            throw "Unable to find retained Azure storage account $SelectedStorageAccount."
        }
    }
    & az storage account delete `
        --name $SelectedStorageAccount `
        --resource-group $SelectedResourceGroup `
        --yes
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to delete retained Azure storage account $SelectedStorageAccount."
    }
    Write-Output "Deleted retained Azure storage account $SelectedStorageAccount and all of its containers."
}

if ($StorageAccount -eq "--all") {
    $All = $true
    $StorageAccount = ""
}

if ($All) {
    $retainedStorageOutput = (& az storage account list `
        --query "[?tags.Project=='opamp' && tags.Purpose=='regression-retention'].[name,resourceGroup]" `
        --output tsv | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to list tagged OpAMP regression retention storage accounts."
    }
    if (-not $retainedStorageOutput) {
        Write-Output "No tagged OpAMP regression retention storage accounts were found."
        exit 0
    }
    $retainedStorageRecords = $retainedStorageOutput -split "\r?\n" | Where-Object { $_ }
    foreach ($retainedStorageRecord in $retainedStorageRecords) {
        $retainedStorageFields = $retainedStorageRecord -split "\s+"
        Remove-RetainedStorageAccount `
            -SelectedStorageAccount $retainedStorageFields[0] `
            -SelectedResourceGroup $retainedStorageFields[1]
    }
    exit 0
}

if (-not $StorageAccount) {
    throw "Provide the retained storage account name, -All, or --all as the first argument."
}

Remove-RetainedStorageAccount -SelectedStorageAccount $StorageAccount
