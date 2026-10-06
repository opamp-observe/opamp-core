#!/usr/bin/env bash
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

set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-opamp-regression-rg}"
NO_WAIT="${NO_WAIT:-true}"

# Delete only the VM resource group. The separate retained storage account and
# its regression evidence require the explicit destroy-bucket command.
if [[ "$NO_WAIT" == "true" ]]; then
  az group delete --name "$RESOURCE_GROUP" --yes --no-wait
else
  az group delete --name "$RESOURCE_GROUP" --yes
fi
echo "Retained Azure storage accounts are not deleted; use cloud/azure/destroy-bucket.sh explicitly."
