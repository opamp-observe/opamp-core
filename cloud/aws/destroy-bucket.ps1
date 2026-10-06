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
    [string]$ArtifactBucketFile = "dist/aws-artifact-bucket.txt"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))

# Omitting the name selects the bucket recorded by the latest deployment. This
# command is intentionally separate because --force removes every stored object.
if (-not [IO.Path]::IsPathRooted($ArtifactBucketFile)) {
    $ArtifactBucketFile = Join-Path $repositoryRoot $ArtifactBucketFile
}
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

& aws s3 rb "s3://$BucketName" --force
if ($LASTEXITCODE -ne 0) {
    throw "Unable to delete retained S3 bucket $BucketName."
}
if (Test-Path -LiteralPath $ArtifactBucketFile -PathType Leaf) {
    $recordedBucketName = (Get-Content -LiteralPath $ArtifactBucketFile -Raw).Trim()
    if ($recordedBucketName -eq $BucketName) {
        Remove-Item -LiteralPath $ArtifactBucketFile -Force
    }
}
Write-Output "Deleted retained S3 bucket $BucketName and all of its objects."
