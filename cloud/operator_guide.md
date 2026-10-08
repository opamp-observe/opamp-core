<!--
Copyright 2026 mp3monster.org
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Cloud deployment operator guide

This guide explains the AWS and Azure deployment automation for an operator who
understands infrastructure as code but is not expected to know either cloud's
product vocabulary. Provider-specific commands and parameters remain in the
[AWS guide](aws/readme.md) and [Azure guide](azure/README.md).

## Mental model

Both implementations create the same logical environment:

1. The workstation builds Python wheels and collects Linux bootstrap scripts.
2. A retained object store receives those deployment artifacts.
3. An infrastructure template creates networking, two Ubuntu VMs, and access
   controls.
4. Each VM downloads the artifacts and runs the shared installer.
5. The server starts the OpAMP services, Keycloak, OAuth2 Proxy, Nginx, and an
   OpenTelemetry Collector.
6. The consumer starts a simulator and an OpenTelemetry Collector.
7. Deployment outputs are converted into a Markdown connection guide and kept
   locally and in retained object storage.

The infrastructure template owns the short-lived compute environment. The
deploy script owns the retained storage. This separation is intentional: an
ordinary infrastructure teardown removes chargeable VMs and networking while
preserving artifacts and regression evidence for later inspection.

## Provider vocabulary

| Purpose | AWS term | Azure term |
|---|---|---|
| Infrastructure definition | CloudFormation template | ARM template |
| Deployment boundary | CloudFormation stack | Resource group deployment |
| Virtual network | VPC and subnet | VNet and subnet |
| VM firewall | Security group | Network security group |
| Virtual machine | EC2 instance | Azure VM |
| Stable public address | Elastic IP | Public IP resource |
| Object storage | S3 bucket | Storage account and blob containers |
| VM bootstrap completion | CloudFormation wait condition | Custom Script Extension status |
| Generated secret | Secrets Manager secret | ARM secure parameter |
| Template result | Stack output | Deployment output |

These terms differ, but their roles in this repository are deliberately kept
parallel.

## Deployment phases

### 1. Preflight

The deploy script resolves repository-relative paths, checks required command
line tools, reads the parameter file, and validates values before creating
resources. AWS can infer an existing EC2 key-pair name from a supplied PEM file
and can detect the caller's public IPv4 address when the example CIDR remains.

### 2. Artifact packaging

Each component is built as a Python wheel. `wheels.txt` is the authoritative
manifest consumed by the VM installer. The package also contains the shared
runtime scripts from `cloud/azure/scripts`.

PowerShell packagers explicitly write UTF-8 without a byte-order mark and use
LF line endings. This matters because the artifacts are executed by Bash on
Linux even when they were produced on Windows.

### 3. Retained storage

When no storage name is supplied, the deploy script creates a timestamped S3
bucket or Azure storage account. Its name is recorded under `dist/` so cleanup
scripts and later deployments can find it. Generated AWS bucket names use a
hyphen-separated UTC timestamp such as `2026-10-05-17-45-30`. Generated Azure
storage account names keep a compact timestamp because Azure storage account
names cannot contain separator characters. Storage is deliberately outside the
template's normal teardown boundary.

The artifact location and retained result location have different exposure:

- AWS artifacts and results remain private and are fetched through VM IAM roles.
- Azure bootstrap artifacts are readable by the VM extension through blob URLs;
  regression results remain in a private container.

### 4. Infrastructure deployment

AWS validates and deploys `cloud/aws/template.yaml`. Azure submits
`cloud/azure/mainTemplate.json` to an ARM resource-group deployment. Both
templates create network controls before VMs and pass artifact locations into
VM bootstrap commands.

### 5. VM bootstrap

The shared `install-opamp.sh` installs operating-system prerequisites, stages
the wheel manifest, creates isolated Python virtual environments, and installs
the wheels needed by the VM's role. The role-specific startup script then
creates configuration files and system services.

AWS user data sends an explicit success or failure signal to CloudFormation.
CloudFormation therefore waits for application bootstrap, not merely EC2
creation. Azure's Custom Script Extension provides the corresponding execution
boundary and reports its status through the ARM deployment.

### 6. Outputs and retained evidence

After infrastructure succeeds, the deploy script requests template outputs and
writes them as JSON. `scripts/generate_cloud_connection_guide.py` normalizes the
different AWS and Azure output shapes into one Markdown document containing
service URLs and SSH commands. Both files are uploaded to retained storage.

## Resource ownership

| Resource | Created by | Normal destroy removes it? | Explicit cleanup |
|---|---|---:|---|
| AWS stack resources | CloudFormation | Yes | `cloud/aws/destroy.*` |
| AWS artifact/results bucket | Deploy script | No | `cloud/aws/destroy-bucket.*` |
| Azure VM resource group | ARM/deploy script | Yes | `cloud/azure/destroy.*` |
| Azure retained storage account | Deploy script | No | `cloud/azure/destroy-bucket.*` |
| Locally generated keys and reports | Deploy script | No | Operator-managed under `dist/` |

Storage cleanup scripts are intentionally separate and destructive: deleting a
bucket or storage account also deletes every retained artifact and result in it.
Passing `--all` to a cleanup script removes only generated OpAMP regression
retention storage for the selected provider. AWS matches the generated
`opamp-regression-<account-id>-<yyyy-mm-dd-hh-mm-ss>` bucket prefix in the
current account, while Azure matches the `Project=opamp` and
`Purpose=regression-retention` storage account tags in the selected
subscription.

## Reading failures

| Failure location | Meaning | First place to inspect |
|---|---|---|
| Packaging before cloud deployment | A wheel or local tool failed | Local command output |
| Template validation | IaC syntax or parameter contract failed | CLI validation message |
| VM resource creation | Cloud capacity, permissions, image, or networking failed | Cloud deployment events |
| AWS wait condition | VM exists but application bootstrap failed | Failed stack event and EC2 console output |
| Azure VM extension | VM exists but downloaded script failed | Extension status and VM boot diagnostics |
| Connection-guide generation | Infrastructure succeeded; local post-processing failed | Output JSON and Python error |
| Result upload | Infrastructure succeeded; retained storage write failed | Local result files and storage permissions |

An infrastructure success followed by a guide or upload error does not require
recreating the VMs. The output JSON can be passed to the guide generator again,
then both files can be uploaded to the existing retained location.

## Safe reruns

- A stack or deployment in a completed state can be updated in place.
- An AWS stack in `ROLLBACK_COMPLETE` must be deleted before redeployment.
- Reusing retained storage overwrites the current artifact object but preserves
  timestamped regression-result prefixes.
- `SKIP_PACKAGE` or `-SkipPackage` is appropriate only when the existing local
  artifact was built from the intended source and has already been validated.
- Never delete retained storage merely to reset compute infrastructure.

## Regression evidence

Infrastructure deployment proves that the environment bootstrapped; it does
not run the local container regression pack. Run and retain a selected test
with `python cloud/run_regression.py --provider <aws|azure> --only <test-id>`.
The command uploads `dist/test-reports/` even when a test fails, then returns
the test process exit code. Use `--upload-only` after a test was run separately.

AWS reads its default bucket from `dist/aws-artifact-bucket.txt`. Azure reads
its default storage account from
`dist/azure-retention-storage-account.txt`. Each upload uses a new UTC result
set and stores evidence below `<result-set>/test-reports/`, including a manifest
that records the destination and regression exit status.

## Main workflow cloud control

`.github/workflows/main_fluent-opamp.yml` always performs its build and uses
the `CLOUD_PROVIDER` GitHub repository variable to select deployment behavior
for pushes to `main`:

| `CLOUD_PROVIDER` | Behavior |
|---|---|
| `azure` | Deploy the existing `fluent-opamp` Azure Web App |
| `aws` | Deploy the AWS CloudFormation regression environment and run the retained regression flow |
| `none` | Complete the build without requesting cloud credentials |
| unset | Use `aws` for pushes to `main`; use `none` for manual `configured` runs |

A manual workflow run can select `azure`, `aws`, or `none` directly. Selecting
`configured` applies the repository variable when it exists and otherwise
performs the build-only `none` flow.

The shared GitHub OIDC helper at
`cloud/aws/scripts/configure_github_oidc_role.py` can configure either provider
by passing `--cloud-provider aws` or `--cloud-provider azure`. With
`--configure-github`, it writes the provider-specific repository secrets and
variables through GitHub's REST API. Azure mode uses the existing
`AZUREAPPSERVICE_CLIENTID_*`, `AZUREAPPSERVICE_TENANTID_*`, and
`AZUREAPPSERVICE_SUBSCRIPTIONID_*` secrets, plus optional `AZURE_APP_NAME` and
`AZURE_RESOURCE_GROUP` variables. AWS mode requires the `AWS_ROLE_TO_ASSUME`
secret and the `AWS_KEY_NAME` and `AWS_ADMIN_SOURCE_CIDR` repository variables.
`AWS_REGION`, `AWS_STACK_NAME`, `AWS_INSTANCE_TYPE`, `AWS_NAME_PREFIX`, and
`AWS_ARTIFACT_BUCKET` are optional AWS repository variables.
`AWS_REGRESSION_ONLY` and `AWS_REGRESSION_SKIP` can contain space-separated
regression test ids when the merge flow should run a focused subset instead of
the full pack. `AWS_REGRESSION_CONTINUE_ON_FAILURE` can be set to `true` to
keep collecting later test evidence after an earlier test fails. Set
`CLOUD_PROVIDER` to `none` if pushes to `main` should stay build-only while the
selected provider's OIDC resources or required repository variables are not
ready. The CloudFormation execution-role secret remains optional.

## Generated local files

| Path | Purpose |
|---|---|
| `dist/opamp-cloud-artifacts.tar.gz` | AWS artifact archive |
| `dist/cloud-azure-artifacts/` | Azure artifact directory |
| `dist/aws-artifact-bucket.txt` | Latest AWS retained bucket name |
| `dist/azure-retention-storage-account.txt` | Latest Azure retained account name |
| `dist/aws-key-pairs/` | Private keys created by the AWS deploy script |
| `dist/*-regression-results/<timestamp>/` | Output JSON and connection guide |
| `dist/test-reports/` | Local regression evidence uploaded by `cloud/run_regression.py` |

Treat private keys and deployment outputs as operational data. They are ignored
by source control and should be protected according to the environment's access
policy.
