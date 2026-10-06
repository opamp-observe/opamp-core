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

STACK_NAME="${STACK_NAME:-opamp-regression}"
AWS_REGION="${AWS_REGION:-eu-west-2}"
WAIT_FOR_DELETE="${WAIT_FOR_DELETE:-true}"
DELETE_POLL_INTERVAL_SECONDS="${DELETE_POLL_INTERVAL_SECONDS:-30}"
DELETE_COMPLETE_STATUS="DELETE_COMPLETE"
DELETE_FAILED_STATUS="DELETE_FAILED"

# Delete only resources owned by CloudFormation. Retained S3 storage has a
# separate destructive command so routine teardown cannot erase evidence.
if [[ ! "$DELETE_POLL_INTERVAL_SECONDS" =~ ^[1-9][0-9]*$ ]]; then
  echo "DELETE_POLL_INTERVAL_SECONDS must be a positive integer." >&2
  exit 1
fi

aws cloudformation delete-stack --region "$AWS_REGION" --stack-name "$STACK_NAME"
if [[ "$WAIT_FOR_DELETE" == "true" ]]; then
  # AWS represents a fully deleted stack by making describe-stacks return a
  # not-found error, so that response is the normal successful terminal state.
  describe_error_file="$(mktemp)"
  trap 'rm -f "$describe_error_file"' EXIT
  while true; do
    if stack_status="$(aws cloudformation describe-stacks \
      --region "$AWS_REGION" \
      --stack-name "$STACK_NAME" \
      --query "Stacks[0].StackStatus" \
      --output text 2> "$describe_error_file")"; then
      if [[ "$stack_status" == "$DELETE_COMPLETE_STATUS" ]]; then
        break
      fi
      if [[ "$stack_status" == "$DELETE_FAILED_STATUS" ]]; then
        echo "CloudFormation reported DELETE_FAILED for $STACK_NAME. Review its stack events." >&2
        exit 1
      fi
      echo "Stack $STACK_NAME status: $stack_status. Checking again in $DELETE_POLL_INTERVAL_SECONDS seconds."
      sleep "$DELETE_POLL_INTERVAL_SECONDS"
      continue
    fi

    describe_error="$(< "$describe_error_file")"
    if [[ "$describe_error" == *"ValidationError"* &&
      "$describe_error" == *"does not exist"* ]]; then
      break
    fi
    echo "Unable to check deletion of $STACK_NAME: $describe_error" >&2
    exit 1
  done
  rm -f "$describe_error_file"
  trap - EXIT
  echo "Deleted CloudFormation stack $STACK_NAME in $AWS_REGION."
else
  echo "Delete requested for CloudFormation stack $STACK_NAME in $AWS_REGION."
fi
echo "Retained S3 buckets are not deleted; use cloud/aws/destroy-bucket.sh explicitly."
