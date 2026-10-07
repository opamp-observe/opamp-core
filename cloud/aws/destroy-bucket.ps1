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
    [string]$BucketName = "",
    [switch]$All,
    [string]$ArtifactBucketFile = "dist/aws-artifact-bucket.txt"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))

if (-not [IO.Path]::IsPathRooted($ArtifactBucketFile)) {
    $ArtifactBucketFile = Join-Path $repositoryRoot $ArtifactBucketFile
}

# Delete one retained S3 bucket and clear the local latest-bucket pointer when it
# points at the bucket that was just removed.
function Remove-RetainedS3Bucket {
    param(
        [Parameter(Mandatory = $true)][string]$SelectedBucketName
    )

    & aws s3 rb "s3://$SelectedBucketName" --force
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to delete retained S3 bucket $SelectedBucketName."
    }
    if (Test-Path -LiteralPath $ArtifactBucketFile -PathType Leaf) {
        $recordedBucketName = (Get-Content -LiteralPath $ArtifactBucketFile -Raw).Trim()
        if ($recordedBucketName -eq $SelectedBucketName) {
            Remove-Item -LiteralPath $ArtifactBucketFile -Force
        }
    }
    Write-Output "Deleted retained S3 bucket $SelectedBucketName and all of its objects."
}

if ($BucketName -eq "--all") {
    $All = $true
    $BucketName = ""
}

if ($All) {
    $awsAccountId = (& aws sts get-caller-identity --query Account --output text | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $awsAccountId) {
        throw "Unable to determine the AWS account ID."
    }
    $bucketNamePrefix = "opamp-regression-$awsAccountId-"
    $retainedBucketOutput = (& aws s3api list-buckets `
        --query "Buckets[?starts_with(Name, '$bucketNamePrefix')].Name" `
        --output text | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to list retained S3 buckets."
    }
    if (-not $retainedBucketOutput) {
        Write-Output "No retained S3 buckets matched prefix $bucketNamePrefix."
        exit 0
    }
    $retainedBuckets = $retainedBucketOutput -split "\s+" | Where-Object { $_ }
    foreach ($retainedBucket in $retainedBuckets) {
        Remove-RetainedS3Bucket -SelectedBucketName $retainedBucket
    }
    exit 0
}

# Omitting the name selects the bucket recorded by the latest deployment. This
# command is intentionally separate because --force removes every stored object.
if (-not $BucketName) {
    if (-not (Test-Path -LiteralPath $ArtifactBucketFile -PathType Leaf)) {
        throw "No bucket name was provided and the latest bucket file was not found: $ArtifactBucketFile"
    }
    $BucketName = (Get-Content -LiteralPath $ArtifactBucketFile -Raw).Trim()
    if (-not $BucketName) {
        throw "The latest bucket file is empty: $ArtifactBucketFile"
    }
    Write-Output "Using latest recorded retained bucket: $BucketName"
}

Remove-RetainedS3Bucket -SelectedBucketName $BucketName
