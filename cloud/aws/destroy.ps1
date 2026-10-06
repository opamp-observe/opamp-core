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
    [string]$StackName = "opamp-regression",
    [string]$AwsRegion = "eu-west-2",
    [int]$PollIntervalSeconds = 30,
    [switch]$NoWait
)

$ErrorActionPreference = "Stop"
$deleteCompleteStatus = "DELETE_COMPLETE"
$deleteFailedStatus = "DELETE_FAILED"

# This script deletes only CloudFormation-owned compute and networking. The S3
# bucket was created outside the stack and is intentionally preserved.
if ($PollIntervalSeconds -lt 1) {
    throw "PollIntervalSeconds must be greater than zero."
}

$previousErrorActionPreference = $ErrorActionPreference
try {
    # Native AWS CLI errors arrive on stderr; capture them so a missing stack can
    # be treated as an idempotent success rather than a PowerShell exception.
    $ErrorActionPreference = "Continue"
    $deleteOutput = & aws cloudformation delete-stack `
        --region $AwsRegion `
        --stack-name $StackName 2>&1
    $deleteExitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $previousErrorActionPreference
}
$deleteText = ($deleteOutput | Out-String).Trim()
$stackAlreadyDeleted = $false
if ($deleteExitCode -ne 0) {
    if ($deleteText.Contains("ValidationError") -and
        $deleteText.Contains("does not exist")) {
        $stackAlreadyDeleted = $true
    } else {
        throw "Unable to request deletion of ${StackName}: $deleteText"
    }
}

if ($stackAlreadyDeleted) {
    Write-Output "CloudFormation stack $StackName no longer exists in $AwsRegion."
} elseif (-not $NoWait) {
    # Polling provides visible progress and catches DELETE_FAILED instead of
    # returning while chargeable resources may still exist.
    while ($true) {
        $previousErrorActionPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = "Continue"
            $describeOutput = & aws cloudformation describe-stacks `
                --region $AwsRegion `
                --stack-name $StackName `
                --query "Stacks[0].StackStatus" `
                --output text 2>&1
            $describeExitCode = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
        $describeText = ($describeOutput | Out-String).Trim()

        if ($describeExitCode -ne 0) {
            if ($describeText.Contains("ValidationError") -and
                $describeText.Contains("does not exist")) {
                break
            }
            throw "Unable to check deletion of ${StackName}: $describeText"
        }
        if ($describeText -eq $deleteCompleteStatus) {
            break
        }
        if ($describeText -eq $deleteFailedStatus) {
            throw "CloudFormation reported DELETE_FAILED for $StackName. Review its stack events."
        }
        Write-Output "Stack $StackName status: $describeText. Checking again in $PollIntervalSeconds seconds."
        Start-Sleep -Seconds $PollIntervalSeconds
    }
    Write-Output "Deleted CloudFormation stack $StackName in $AwsRegion."
} else {
    Write-Output "Delete requested for CloudFormation stack $StackName in $AwsRegion."
}
Write-Output "Retained S3 buckets are not deleted; use cloud/aws/destroy-bucket.ps1 explicitly."
