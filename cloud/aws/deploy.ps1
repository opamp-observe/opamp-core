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
    [string]$ArtifactBucket = "",
    [string]$ArtifactKey = "opamp-cloud/opamp-cloud-artifacts.tar.gz",
    [string]$TemplateFile = "cloud/aws/template.yaml",
    [string]$ParametersFile = "cloud/aws/parameters.example.env",
    [string]$ArtifactArchive = "dist/opamp-cloud-artifacts.tar.gz",
    [string]$ArtifactBucketFile = "dist/aws-artifact-bucket.txt",
    [string]$CloudFormationRoleArn = "",
    [string]$RegressionResultsPrefix = "regression-results",
    [switch]$CreateKeyPair,
    [string]$NewKeyPairName = "",
    [string]$PrivateKeyFile = "",
    [switch]$SkipPackage
)

# Orchestrate the complete AWS deployment from the operator workstation. The
# CloudFormation template owns compute and networking; this script owns artifact
# packaging, retained S3 storage, parameter preparation, and result capture.
$ErrorActionPreference = "Stop"
$deploymentTimestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmss")
$retainedBucketTimestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd-HH-mm-ss")
$adminSourceCidrParameter = "AdminSourceCidr"
$adminSourceCidrPrefixLength = 32
$failedStackEventsQuery = "StackEvents[?contains(ResourceStatus, 'FAILED')].[Timestamp,LogicalResourceId,ResourceType,ResourceStatus,ResourceStatusReason]"
$keyNameParameter = "KeyName"
$publicIpLookupUri = "https://checkip.amazonaws.com"
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$utf8NoBomEncoding = New-Object System.Text.UTF8Encoding -ArgumentList $false

# Phase 1: resolve caller-supplied paths relative to the repository. This keeps
# behavior stable when the script is launched from another working directory.
if (-not [IO.Path]::IsPathRooted($TemplateFile)) {
    $TemplateFile = Join-Path $repositoryRoot $TemplateFile
}
if (-not [IO.Path]::IsPathRooted($ParametersFile)) {
    $ParametersFile = Join-Path $repositoryRoot $ParametersFile
}
if (-not [IO.Path]::IsPathRooted($ArtifactArchive)) {
    $ArtifactArchive = Join-Path $repositoryRoot $ArtifactArchive
}
if (-not [IO.Path]::IsPathRooted($ArtifactBucketFile)) {
    $ArtifactBucketFile = Join-Path $repositoryRoot $ArtifactBucketFile
}
if ($PrivateKeyFile -and -not [IO.Path]::IsPathRooted($PrivateKeyFile)) {
    $PrivateKeyFile = Join-Path $repositoryRoot $PrivateKeyFile
}

# Phase 2: validate local tools and translate the simple NAME=VALUE file into
# the parameter override format expected by CloudFormation.
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI is required."
}
$pythonCommand = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
$pythonArguments = if ($pythonCommand -eq "py") { @("-3") } else { @() }
if (-not (Test-Path -LiteralPath $ParametersFile)) {
    throw "Parameter file not found: $ParametersFile"
}

$parameterOverrides = @()
$selectedKeyPairName = ""
$privateKeyFileKeyPairName = ""
if ($PrivateKeyFile) {
    if (-not (Test-Path -LiteralPath $PrivateKeyFile -PathType Leaf)) {
        throw "Private key file not found: $PrivateKeyFile"
    }
    $privateKeyFileKeyPairName = [IO.Path]::GetFileNameWithoutExtension($PrivateKeyFile)
}
foreach ($parameterLine in Get-Content -LiteralPath $ParametersFile) {
    $trimmedLine = $parameterLine.Trim()
    if (-not $trimmedLine -or $trimmedLine.StartsWith("#")) {
        continue
    }
    if (-not $trimmedLine.Contains("=")) {
        throw "Invalid parameter line: $trimmedLine"
    }
    $parameterName, $parameterValue = $trimmedLine.Split("=", 2)
    if ($parameterName -eq $keyNameParameter -and $CreateKeyPair) {
        if ($NewKeyPairName) {
            $parameterValue = $NewKeyPairName
        } elseif ($parameterValue.StartsWith("REPLACE_")) {
            $parameterValue = "$StackName-$deploymentTimestamp"
        }
    } elseif ($parameterName -eq $keyNameParameter -and
        $parameterValue.StartsWith("REPLACE_") -and
        $privateKeyFileKeyPairName) {
        $parameterValue = $privateKeyFileKeyPairName
        Write-Output "Using EC2 key pair inferred from private key file: $parameterValue"
    }
    if ($parameterName -eq $keyNameParameter) {
        $selectedKeyPairName = $parameterValue
    }
    if ($parameterValue.StartsWith("REPLACE_")) {
        if ($parameterName -eq $keyNameParameter) {
            throw "Set KeyName in $ParametersFile to an existing EC2 key pair in $AwsRegion. " +
                "List key pairs with: aws ec2 describe-key-pairs --region $AwsRegion " +
                "--query `"KeyPairs[].KeyName`" --output table"
        }
        if ($parameterName -eq $adminSourceCidrParameter) {
            try {
                $detectedPublicIp = (Invoke-RestMethod `
                    -Uri $publicIpLookupUri `
                    -UseBasicParsing).ToString().Trim()
            } catch {
                throw "Unable to detect the public IPv4 address from $publicIpLookupUri. " +
                    "Set AdminSourceCidr in $ParametersFile manually. $($_.Exception.Message)"
            }
            $parsedPublicIp = $null
            if (-not [System.Net.IPAddress]::TryParse($detectedPublicIp, [ref]$parsedPublicIp) -or
                $parsedPublicIp.AddressFamily -ne
                [System.Net.Sockets.AddressFamily]::InterNetwork) {
                throw "The public address service returned a non-IPv4 value: $detectedPublicIp. " +
                    "Set AdminSourceCidr in $ParametersFile manually."
            }
            $parameterValue = "$detectedPublicIp/$adminSourceCidrPrefixLength"
            Write-Output "Detected administrator source CIDR: $parameterValue"
        } else {
            throw "Replace the placeholder value for $parameterName in $ParametersFile"
        }
    }
    $parameterOverrides += "$parameterName=$parameterValue"
}

# Confirm an existing EC2 key pair before packaging or creating cloud resources.
# The PEM stays local; EC2 stores only the corresponding public key.
if (-not $CreateKeyPair) {
    $matchingKeyPairCount = (& aws ec2 describe-key-pairs `
        --region $AwsRegion `
        --filters "Name=key-name,Values=$selectedKeyPairName" `
        --query "length(KeyPairs)" `
        --output text | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $matchingKeyPairCount -ne "1") {
        throw "EC2 key pair $selectedKeyPairName was not found in $AwsRegion."
    }
}

if ($CreateKeyPair) {
    if (-not $selectedKeyPairName) {
        throw "The parameter file must contain KeyName when -CreateKeyPair is used."
    }
    if (-not $PrivateKeyFile) {
        $PrivateKeyFile = Join-Path $repositoryRoot "dist/aws-key-pairs/$selectedKeyPairName.pem"
    }
    if (Test-Path -LiteralPath $PrivateKeyFile) {
        throw "Private key file already exists and will not be overwritten: $PrivateKeyFile"
    }
    $privateKeyDirectory = Split-Path -Parent $PrivateKeyFile
    if ($privateKeyDirectory) {
        New-Item -ItemType Directory -Path $privateKeyDirectory -Force | Out-Null
    }
    $privateKeyMaterial = (& aws ec2 create-key-pair `
        --region $AwsRegion `
        --key-name $selectedKeyPairName `
        --tag-specifications `
        "ResourceType=key-pair,Tags=[{Key=Project,Value=opamp},{Key=Purpose,Value=regression-access}]" `
        --query KeyMaterial `
        --output text | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $privateKeyMaterial) {
        throw "Unable to create EC2 key pair $selectedKeyPairName in $AwsRegion."
    }
    try {
        [IO.File]::WriteAllText(
            $PrivateKeyFile,
            "$privateKeyMaterial`n",
            $utf8NoBomEncoding
        )
        if ($env:OS -eq "Windows_NT") {
            $currentIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
            & icacls.exe $PrivateKeyFile /inheritance:r /grant:r "${currentIdentity}:(R)" | Out-Null
        } else {
            & chmod 600 $PrivateKeyFile
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to restrict private key permissions."
        }
    } catch {
        & aws ec2 delete-key-pair `
            --region $AwsRegion `
            --key-name $selectedKeyPairName | Out-Null
        Remove-Item -LiteralPath $PrivateKeyFile -Force -ErrorAction SilentlyContinue
        throw "Unable to store the private key; the generated AWS key pair was removed. $($_.Exception.Message)"
    }
    Write-Output "Created EC2 key pair $selectedKeyPairName"
    Write-Output "Private key: $PrivateKeyFile"
}

# Phase 3: create retained object storage outside CloudFormation, or reuse the
# supplied bucket. Stack deletion intentionally cannot delete this evidence.
if (-not $ArtifactBucket) {
    $awsAccountId = (& aws sts get-caller-identity --query Account --output text | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $awsAccountId) {
        throw "Unable to determine the AWS account ID."
    }
    $ArtifactBucket = "opamp-regression-$awsAccountId-$retainedBucketTimestamp"
    if ($AwsRegion -eq "us-east-1") {
        & aws s3api create-bucket --bucket $ArtifactBucket --region $AwsRegion | Out-Null
    } else {
        & aws s3api create-bucket `
            --bucket $ArtifactBucket `
            --region $AwsRegion `
            --create-bucket-configuration "LocationConstraint=$AwsRegion" | Out-Null
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create retained S3 bucket $ArtifactBucket."
    }
    & aws s3api put-public-access-block `
        --bucket $ArtifactBucket `
        --region $AwsRegion `
        --public-access-block-configuration `
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to block public access to $ArtifactBucket."
    }
    & aws s3api put-bucket-tagging `
        --bucket $ArtifactBucket `
        --region $AwsRegion `
        --tagging `
        "TagSet=[{Key=Project,Value=opamp},{Key=Purpose,Value=regression-retention},{Key=CreatedAt,Value=$deploymentTimestamp}]"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to tag $ArtifactBucket."
    }
    Write-Output "Created retained S3 bucket $ArtifactBucket"
} else {
    Write-Output "Using retained S3 bucket $ArtifactBucket"
}
$artifactBucketDirectory = Split-Path -Parent $ArtifactBucketFile
if ($artifactBucketDirectory) {
    New-Item -ItemType Directory -Path $artifactBucketDirectory -Force | Out-Null
}
[IO.File]::WriteAllText(
    $ArtifactBucketFile,
    "$ArtifactBucket`r`n",
    $utf8NoBomEncoding
)

# Phase 4: build wheels and Linux bootstrap scripts, then upload the single
# archive that the EC2 instance roles are permitted to read.
if (-not $SkipPackage) {
    & (Join-Path $PSScriptRoot "scripts\package-cloud-artifacts.ps1") -ArchivePath $ArtifactArchive
}
if (-not (Test-Path -LiteralPath $ArtifactArchive)) {
    throw "Artifact archive not found: $ArtifactArchive"
}

& aws s3 cp $ArtifactArchive "s3://$ArtifactBucket/$ArtifactKey" --region $AwsRegion --only-show-errors
if ($LASTEXITCODE -ne 0) {
    throw "Unable to upload deployment artifacts."
}

$parameterOverrides += "ArtifactBucket=$ArtifactBucket"
$parameterOverrides += "ArtifactKey=$ArtifactKey"

# Phase 5: validate and deploy the infrastructure template. CloudFormation wait
# conditions keep this call open until both VMs report application bootstrap.
$resolvedTemplatePath = (Resolve-Path $TemplateFile).Path.Replace("\", "/")
& aws cloudformation validate-template --region $AwsRegion --template-body "file://$resolvedTemplatePath" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "CloudFormation template validation failed."
}

$deployArguments = @(
    "cloudformation", "deploy",
    "--region", $AwsRegion,
    "--stack-name", $StackName,
    "--template-file", $TemplateFile,
    "--parameter-overrides"
) + $parameterOverrides + @(
    "--capabilities", "CAPABILITY_IAM",
    "--no-fail-on-empty-changeset",
    "--tags", "Project=opamp", "ManagedBy=cloudformation"
)
if ($CloudFormationRoleArn) {
    $deployArguments += @("--role-arn", $CloudFormationRoleArn)
}
& aws @deployArguments
if ($LASTEXITCODE -ne 0) {
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $failureEvents = & aws cloudformation describe-stack-events `
            --region $AwsRegion `
            --stack-name $StackName `
            --query $failedStackEventsQuery `
            --output table 2>&1
        $failureEventsExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($failureEventsExitCode -eq 0) {
        Write-Output "CloudFormation failed resource events:"
        Write-Output $failureEvents
    } else {
        $failureEventsError = ($failureEvents | Out-String).Trim()
        Write-Warning "Unable to retrieve CloudFormation failure events: $failureEventsError"
    }
    throw "CloudFormation deployment failed. Review the failed resource events above."
}

# Phase 6: template success is complete at this point. The remaining work is
# retryable post-processing: save outputs, render the guide, and retain both.
$resultsDirectory = Join-Path $repositoryRoot "dist/aws-regression-results/$deploymentTimestamp"
$connectionGuideFile = Join-Path $resultsDirectory "connection_details.md"
$stackOutputsFile = Join-Path $resultsDirectory "stack-outputs.json"
New-Item -ItemType Directory -Path $resultsDirectory -Force | Out-Null
$stackOutputs = & aws cloudformation describe-stacks `
    --region $AwsRegion `
    --stack-name $StackName `
    --query "Stacks[0].Outputs" `
    --output json
if ($LASTEXITCODE -ne 0) {
    throw "Unable to retain CloudFormation outputs."
}
[IO.File]::WriteAllLines(
    $stackOutputsFile,
    [string[]]$stackOutputs,
    $utf8NoBomEncoding
)
$connectionGuideArguments = @(
    (Join-Path $repositoryRoot "scripts/generate_cloud_connection_guide.py"),
    "--provider", "aws",
    "--outputs-file", $stackOutputsFile,
    "--output-file", $connectionGuideFile
)
if ($PrivateKeyFile) {
    $connectionGuideArguments += @("--ssh-private-key", $PrivateKeyFile)
}
$pythonInvocationArguments = @($pythonArguments) + $connectionGuideArguments
& $pythonCommand @pythonInvocationArguments
if ($LASTEXITCODE -ne 0 -or
    -not (Test-Path -LiteralPath $connectionGuideFile -PathType Leaf) -or
    (Get-Item -LiteralPath $connectionGuideFile).Length -eq 0) {
    throw "Unable to generate the AWS connection guide."
}
& aws s3 cp `
    $stackOutputsFile `
    "s3://$ArtifactBucket/$RegressionResultsPrefix/$deploymentTimestamp/stack-outputs.json" `
    --region $AwsRegion `
    --only-show-errors
if ($LASTEXITCODE -ne 0) {
    throw "Unable to upload retained deployment results."
}
& aws s3 cp `
    $connectionGuideFile `
    "s3://$ArtifactBucket/$RegressionResultsPrefix/$deploymentTimestamp/connection_details.md" `
    --region $AwsRegion `
    --only-show-errors
if ($LASTEXITCODE -ne 0) {
    throw "Unable to upload the AWS connection guide."
}

& aws cloudformation describe-stacks `
    --region $AwsRegion `
    --stack-name $StackName `
    --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" `
    --output table
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read CloudFormation outputs."
}
Write-Output "Retained bucket: $ArtifactBucket"
Write-Output "Retained deployment results: s3://$ArtifactBucket/$RegressionResultsPrefix/$deploymentTimestamp/"
Write-Output "Connection guide: $connectionGuideFile"
