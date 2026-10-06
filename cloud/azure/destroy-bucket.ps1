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
    [Parameter(Mandatory = $true)][string]$StorageAccount
)

$ErrorActionPreference = "Stop"

# Resolve the owning resource group before deletion because Azure storage account
# names are globally unique but deletion is scoped to their resource group.
$storageResourceGroup = (& az storage account show `
    --name $StorageAccount `
    --query resourceGroup `
    --output tsv | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $storageResourceGroup) {
    throw "Unable to find retained Azure storage account $StorageAccount."
}
& az storage account delete `
    --name $StorageAccount `
    --resource-group $storageResourceGroup `
    --yes
if ($LASTEXITCODE -ne 0) {
    throw "Unable to delete retained Azure storage account $StorageAccount."
}
Write-Output "Deleted retained Azure storage account $StorageAccount and all of its containers."
