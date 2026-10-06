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

# Orchestrate packaging, retained storage, CloudFormation, and output capture
# from the operator workstation. VM configuration is delegated to template user data.
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
STACK_NAME="${STACK_NAME:-opamp-regression}"
AWS_REGION="${AWS_REGION:-eu-west-2}"
TEMPLATE_FILE="${TEMPLATE_FILE:-$REPO_ROOT/cloud/aws/template.yaml}"
PARAMETERS_FILE="${PARAMETERS_FILE:-$REPO_ROOT/cloud/aws/parameters.example.env}"
ARTIFACT_BUCKET="${ARTIFACT_BUCKET:-}"
ARTIFACT_KEY="${ARTIFACT_KEY:-opamp-cloud/opamp-cloud-artifacts.tar.gz}"
ARTIFACT_ARCHIVE="${ARTIFACT_ARCHIVE:-$REPO_ROOT/dist/opamp-cloud-artifacts.tar.gz}"
ARTIFACT_BUCKET_FILE="${ARTIFACT_BUCKET_FILE:-$REPO_ROOT/dist/aws-artifact-bucket.txt}"
CLOUDFORMATION_ROLE_ARN="${CLOUDFORMATION_ROLE_ARN:-}"
REGRESSION_RESULTS_PREFIX="${REGRESSION_RESULTS_PREFIX:-regression-results}"
SKIP_PACKAGE="${SKIP_PACKAGE:-false}"
CREATE_KEY_PAIR="${CREATE_KEY_PAIR:-false}"
NEW_KEY_PAIR_NAME="${NEW_KEY_PAIR_NAME:-}"
PRIVATE_KEY_FILE="${PRIVATE_KEY_FILE:-}"
DEPLOYMENT_TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
KEY_NAME_PARAMETER="KeyName"
ADMIN_SOURCE_CIDR_PARAMETER="AdminSourceCidr"
ADMIN_SOURCE_CIDR_PREFIX_LENGTH="32"
FAILED_STACK_EVENTS_QUERY="StackEvents[?contains(ResourceStatus, 'FAILED')].[Timestamp,LogicalResourceId,ResourceType,ResourceStatus,ResourceStatusReason]"
PUBLIC_IP_LOOKUP_TIMEOUT_SECONDS="10"
PUBLIC_IP_LOOKUP_URI="https://checkip.amazonaws.com"

# Phase 1: fail before creating resources when local tools or inputs are missing.
for required_command in aws python tar; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "$required_command is required." >&2
    exit 1
  fi
done
if [[ ! -f "$PARAMETERS_FILE" ]]; then
  echo "Parameter file not found: $PARAMETERS_FILE" >&2
  exit 1
fi
if [[ "$CREATE_KEY_PAIR" != "true" && "$CREATE_KEY_PAIR" != "false" ]]; then
  echo "CREATE_KEY_PAIR must be true or false." >&2
  exit 1
fi

parameter_overrides=()
selected_key_pair_name=""
private_key_file_key_pair_name=""
# Phase 2: translate NAME=VALUE parameters into CloudFormation overrides. A
# supplied PEM may resolve the placeholder KeyName, but private material is never uploaded.
if [[ -n "$PRIVATE_KEY_FILE" ]]; then
  if [[ ! -f "$PRIVATE_KEY_FILE" ]]; then
    echo "Private key file not found: $PRIVATE_KEY_FILE" >&2
    exit 1
  fi
  private_key_file_name="$(basename "$PRIVATE_KEY_FILE")"
  private_key_file_key_pair_name="${private_key_file_name%.pem}"
fi
while IFS= read -r parameter_line || [[ -n "$parameter_line" ]]; do
  [[ -z "$parameter_line" || "$parameter_line" == \#* ]] && continue
  if [[ "$parameter_line" != *=* ]]; then
    echo "Invalid parameter line: $parameter_line" >&2
    exit 1
  fi
  parameter_name="${parameter_line%%=*}"
  parameter_value="${parameter_line#*=}"
  if [[ "$parameter_name" == "$KEY_NAME_PARAMETER" && "$CREATE_KEY_PAIR" == "true" ]]; then
    if [[ -n "$NEW_KEY_PAIR_NAME" ]]; then
      parameter_value="$NEW_KEY_PAIR_NAME"
    elif [[ "$parameter_value" == REPLACE_* ]]; then
      parameter_value="$STACK_NAME-$DEPLOYMENT_TIMESTAMP"
    fi
  elif [[ "$parameter_name" == "$KEY_NAME_PARAMETER" &&
    "$parameter_value" == REPLACE_* && -n "$private_key_file_key_pair_name" ]]; then
    parameter_value="$private_key_file_key_pair_name"
    echo "Using EC2 key pair inferred from private key file: $parameter_value"
  fi
  if [[ "$parameter_name" == "$KEY_NAME_PARAMETER" ]]; then
    selected_key_pair_name="$parameter_value"
  fi
  if [[ "$parameter_value" == REPLACE_* ]]; then
    if [[ "$parameter_name" == "$KEY_NAME_PARAMETER" ]]; then
      echo "Set KeyName in $PARAMETERS_FILE to an existing EC2 key pair in $AWS_REGION." >&2
      echo "List key pairs with: aws ec2 describe-key-pairs --region $AWS_REGION --query 'KeyPairs[].KeyName' --output table" >&2
      exit 1
    fi
    if [[ "$parameter_name" == "$ADMIN_SOURCE_CIDR_PARAMETER" ]]; then
      if ! detected_public_ip="$(python -c \
        'import sys; from ipaddress import IPv4Address; from urllib.request import urlopen; response = urlopen(sys.argv[1], timeout=int(sys.argv[2])).read().decode("ascii").strip(); print(IPv4Address(response))' \
        "$PUBLIC_IP_LOOKUP_URI" "$PUBLIC_IP_LOOKUP_TIMEOUT_SECONDS")"; then
        echo "Unable to detect the public IPv4 address from $PUBLIC_IP_LOOKUP_URI." >&2
        echo "Set AdminSourceCidr in $PARAMETERS_FILE manually." >&2
        exit 1
      fi
      parameter_value="$detected_public_ip/$ADMIN_SOURCE_CIDR_PREFIX_LENGTH"
      echo "Detected administrator source CIDR: $parameter_value"
    else
      echo "Replace the placeholder value for $parameter_name in $PARAMETERS_FILE" >&2
      exit 1
    fi
  fi
  parameter_overrides+=("$parameter_name=$parameter_value")
done < "$PARAMETERS_FILE"

if [[ "$CREATE_KEY_PAIR" == "false" ]]; then
  matching_key_pair_count="$(aws ec2 describe-key-pairs \
    --region "$AWS_REGION" \
    --filters "Name=key-name,Values=$selected_key_pair_name" \
    --query 'length(KeyPairs)' \
    --output text)"
  if [[ "$matching_key_pair_count" != "1" ]]; then
    echo "EC2 key pair $selected_key_pair_name was not found in $AWS_REGION." >&2
    exit 1
  fi
fi

# Create an EC2 key pair and securely store its one-time private material.
# The first parameter is the AWS key pair name and the second is the local PEM path.
create_ec2_key_pair() {
  local key_pair_name="$1"
  local private_key_file="$2"
  local private_key_material

  if [[ -e "$private_key_file" ]]; then
    echo "Private key file already exists and will not be overwritten: $private_key_file" >&2
    return 1
  fi
  mkdir -p "$(dirname "$private_key_file")"
  if ! private_key_material="$(aws ec2 create-key-pair \
    --region "$AWS_REGION" \
    --key-name "$key_pair_name" \
    --tag-specifications \
      'ResourceType=key-pair,Tags=[{Key=Project,Value=opamp},{Key=Purpose,Value=regression-access}]' \
    --query KeyMaterial \
    --output text)"; then
    echo "Unable to create EC2 key pair $key_pair_name in $AWS_REGION." >&2
    return 1
  fi
  if ! printf "%s\n" "$private_key_material" > "$private_key_file" ||
    ! chmod 600 "$private_key_file"; then
    aws ec2 delete-key-pair --region "$AWS_REGION" --key-name "$key_pair_name" >/dev/null || true
    rm -f "$private_key_file"
    echo "Unable to store the private key; the generated AWS key pair was removed." >&2
    return 1
  fi
  echo "Created EC2 key pair $key_pair_name"
  echo "Private key: $private_key_file"
}

if [[ "$CREATE_KEY_PAIR" == "true" ]]; then
  if [[ -z "$selected_key_pair_name" ]]; then
    echo "The parameter file must contain KeyName when CREATE_KEY_PAIR=true." >&2
    exit 1
  fi
  PRIVATE_KEY_FILE="${PRIVATE_KEY_FILE:-$REPO_ROOT/dist/aws-key-pairs/$selected_key_pair_name.pem}"
  if [[ "$PRIVATE_KEY_FILE" != /* ]]; then
    PRIVATE_KEY_FILE="$REPO_ROOT/$PRIVATE_KEY_FILE"
  fi
  create_ec2_key_pair "$selected_key_pair_name" "$PRIVATE_KEY_FILE"
fi

# Create private retained storage when the caller has not supplied a bucket.
# The first parameter is the globally unique bucket name to create.
create_artifact_bucket() {
  local bucket_name="$1"
  if [[ "$AWS_REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$bucket_name" --region "$AWS_REGION" >/dev/null
  else
    aws s3api create-bucket \
      --bucket "$bucket_name" \
      --region "$AWS_REGION" \
      --create-bucket-configuration "LocationConstraint=$AWS_REGION" >/dev/null
  fi
  aws s3api put-public-access-block \
    --bucket "$bucket_name" \
    --region "$AWS_REGION" \
    --public-access-block-configuration \
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-tagging \
    --bucket "$bucket_name" \
    --region "$AWS_REGION" \
    --tagging \
      "TagSet=[{Key=Project,Value=opamp},{Key=Purpose,Value=regression-retention},{Key=CreatedAt,Value=$DEPLOYMENT_TIMESTAMP}]"
}

# Phase 3: retained S3 storage is deliberately outside the stack lifecycle so
# regression evidence survives ordinary infrastructure deletion.
if [[ -z "$ARTIFACT_BUCKET" ]]; then
  aws_account_id="$(aws sts get-caller-identity --query Account --output text)"
  ARTIFACT_BUCKET="opamp-regression-${aws_account_id}-${DEPLOYMENT_TIMESTAMP}"
  create_artifact_bucket "$ARTIFACT_BUCKET"
  echo "Created retained S3 bucket $ARTIFACT_BUCKET"
else
  echo "Using retained S3 bucket $ARTIFACT_BUCKET"
fi
mkdir -p "$(dirname "$ARTIFACT_BUCKET_FILE")"
printf "%s\n" "$ARTIFACT_BUCKET" > "$ARTIFACT_BUCKET_FILE"

# Phase 4: build and upload the archive consumed by EC2 user data.
if [[ "$SKIP_PACKAGE" != "true" ]]; then
  REPO_ROOT="$REPO_ROOT" ARCHIVE_PATH="$ARTIFACT_ARCHIVE" \
    bash "$REPO_ROOT/cloud/aws/scripts/package-cloud-artifacts.sh"
fi
if [[ ! -f "$ARTIFACT_ARCHIVE" ]]; then
  echo "Artifact archive not found: $ARTIFACT_ARCHIVE" >&2
  exit 1
fi

aws s3 cp "$ARTIFACT_ARCHIVE" "s3://$ARTIFACT_BUCKET/$ARTIFACT_KEY" \
  --region "$AWS_REGION" --only-show-errors

parameter_overrides+=("ArtifactBucket=$ARTIFACT_BUCKET" "ArtifactKey=$ARTIFACT_KEY")

# Phase 5: CloudFormation creates infrastructure and waits for explicit server
# and consumer bootstrap signals before returning success.
aws cloudformation validate-template \
  --region "$AWS_REGION" \
  --template-body "file://$TEMPLATE_FILE" >/dev/null

deploy_arguments=(
  cloudformation deploy
  --region "$AWS_REGION"
  --stack-name "$STACK_NAME"
  --template-file "$TEMPLATE_FILE"
  --parameter-overrides "${parameter_overrides[@]}"
  --capabilities CAPABILITY_IAM
  --no-fail-on-empty-changeset
  --tags Project=opamp ManagedBy=cloudformation
)
if [[ -n "$CLOUDFORMATION_ROLE_ARN" ]]; then
  deploy_arguments+=(--role-arn "$CLOUDFORMATION_ROLE_ARN")
fi
if ! aws "${deploy_arguments[@]}"; then
  echo "CloudFormation failed resource events:" >&2
  if ! aws cloudformation describe-stack-events \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "$FAILED_STACK_EVENTS_QUERY" \
    --output table >&2; then
    echo "Unable to retrieve CloudFormation failure events." >&2
  fi
  echo "CloudFormation deployment failed. Review the failed resource events above." >&2
  exit 1
fi

# Phase 6: save provider outputs and a human-readable guide locally and in S3.
# These steps can be repeated without recreating a successful stack.
results_directory="$REPO_ROOT/dist/aws-regression-results/$DEPLOYMENT_TIMESTAMP"
connection_guide_file="$results_directory/connection_details.md"
stack_outputs_file="$results_directory/stack-outputs.json"
mkdir -p "$results_directory"
aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output json > "$stack_outputs_file"
python "$REPO_ROOT/scripts/generate_cloud_connection_guide.py" \
  --provider aws \
  --outputs-file "$stack_outputs_file" \
  --output-file "$connection_guide_file" \
  --ssh-private-key "$PRIVATE_KEY_FILE"
aws s3 cp \
  "$stack_outputs_file" \
  "s3://$ARTIFACT_BUCKET/$REGRESSION_RESULTS_PREFIX/$DEPLOYMENT_TIMESTAMP/stack-outputs.json" \
  --region "$AWS_REGION" \
  --only-show-errors
aws s3 cp \
  "$connection_guide_file" \
  "s3://$ARTIFACT_BUCKET/$REGRESSION_RESULTS_PREFIX/$DEPLOYMENT_TIMESTAMP/connection_details.md" \
  --region "$AWS_REGION" \
  --only-show-errors

aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" \
  --output table
echo "Retained bucket: $ARTIFACT_BUCKET"
echo "Retained deployment results: s3://$ARTIFACT_BUCKET/$REGRESSION_RESULTS_PREFIX/$DEPLOYMENT_TIMESTAMP/"
echo "Connection guide: $connection_guide_file"
