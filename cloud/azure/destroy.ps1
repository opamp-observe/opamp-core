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
    [switch]$Wait
)

$ErrorActionPreference = "Stop"

# Delete the VM resource group while preserving the separate retention resource
# group. -Wait is useful when a caller must confirm billing resources are gone.
if ($Wait) {
    az group delete --name $ResourceGroup --yes | Out-Host
} else {
    az group delete --name $ResourceGroup --yes --no-wait | Out-Host
}
Write-Output "Retained Azure storage accounts are not deleted; use cloud/azure/destroy-bucket.ps1 explicitly."
