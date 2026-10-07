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

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
BUCKET_NAME="${BUCKET_NAME:-${1:-}}"
ARTIFACT_BUCKET_FILE="${ARTIFACT_BUCKET_FILE:-$REPO_ROOT/dist/aws-artifact-bucket.txt}"
DELETE_ALL_RETAINED_BUCKETS=false
if [[ "$BUCKET_NAME" == "--all" ]]; then
  DELETE_ALL_RETAINED_BUCKETS=true
  BUCKET_NAME=""
fi

# Delete one retained S3 bucket and clear the local latest-bucket pointer when it
# points at the bucket that was just removed.
delete_retained_bucket() {
  local bucket_name="$1"
  aws s3 rb "s3://$bucket_name" --force
  if [[ -f "$ARTIFACT_BUCKET_FILE" ]] &&
    [[ "$(< "$ARTIFACT_BUCKET_FILE")" == "$bucket_name" ]]; then
    rm -f "$ARTIFACT_BUCKET_FILE"
  fi
  echo "Deleted retained S3 bucket $bucket_name and all of its objects."
}

if [[ "$DELETE_ALL_RETAINED_BUCKETS" == "true" ]]; then
  aws_account_id="$(aws sts get-caller-identity --query Account --output text)"
  bucket_name_prefix="opamp-regression-${aws_account_id}-"
  mapfile -t retained_buckets < <(
    aws s3api list-buckets \
      --query "Buckets[?starts_with(Name, \`$bucket_name_prefix\`)].Name" \
      --output text | tr '\t' '\n' | sed '/^$/d'
  )
  if [[ "${#retained_buckets[@]}" -eq 0 ]]; then
    echo "No retained S3 buckets matched prefix $bucket_name_prefix."
    exit 0
  fi
  for retained_bucket in "${retained_buckets[@]}"; do
    delete_retained_bucket "$retained_bucket"
  done
  exit 0
fi

# Omitting the name selects the latest recorded bucket. The command below is
# destructive: --force deletes all artifacts and regression results first.
if [[ -z "$BUCKET_NAME" ]]; then
  if [[ ! -f "$ARTIFACT_BUCKET_FILE" ]]; then
    echo "No bucket name was provided and the latest bucket file was not found: $ARTIFACT_BUCKET_FILE" >&2
    exit 1
  fi
  BUCKET_NAME="$(< "$ARTIFACT_BUCKET_FILE")"
  if [[ -z "$BUCKET_NAME" ]]; then
    echo "The latest bucket file is empty: $ARTIFACT_BUCKET_FILE" >&2
    exit 1
  fi
  echo "Using latest recorded retained bucket: $BUCKET_NAME"
fi

delete_retained_bucket "$BUCKET_NAME"
