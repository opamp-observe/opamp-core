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

"""Convert provider deployment outputs into one operator connection guide.

AWS CloudFormation and Azure Resource Manager serialize outputs differently.
This module isolates that provider-specific parsing so the deployment scripts
can retain one consistent Markdown artifact containing service URLs and SSH
commands. It does not call either cloud API; callers first save deployment
outputs as JSON and then pass the local file to this command.
"""

import argparse
import json
import shlex
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

AWS_PROVIDER = "aws"
AZURE_PROVIDER = "azure"
SUPPORTED_PROVIDERS = (AWS_PROVIDER, AZURE_PROVIDER)

AWS_OUTPUT_KEY = "OutputKey"
AWS_OUTPUT_VALUE = "OutputValue"
AZURE_OUTPUT_VALUE = "value"

OPAMP_URL_KEY = "opamp_url"
KEYCLOAK_URL_KEY = "keycloak_url"
SERVER_SSH_KEY = "server_ssh"
CONSUMER_SSH_KEY = "consumer_ssh"

OUTPUT_NAMES = {
    AWS_PROVIDER: {
        OPAMP_URL_KEY: "OpampUiUrl",
        KEYCLOAK_URL_KEY: "KeycloakUrl",
        SERVER_SSH_KEY: "ServerSsh",
        CONSUMER_SSH_KEY: "ConsumerSsh",
    },
    AZURE_PROVIDER: {
        OPAMP_URL_KEY: "opampUiUrl",
        KEYCLOAK_URL_KEY: "keycloakUrl",
        SERVER_SSH_KEY: "serverSsh",
        CONSUMER_SSH_KEY: "consumerSsh",
    },
}


def _parse_arguments() -> argparse.Namespace:
    """Parse command-line locations and the provider output format.

    Returns:
        The validated provider name, input JSON path, output Markdown path, and
        optional local SSH private-key path.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=SUPPORTED_PROVIDERS, required=True)
    parser.add_argument("--outputs-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--ssh-private-key", default="")
    return parser.parse_args()


def _load_output_values(provider: str, outputs_file: Path) -> dict[str, str]:
    """Normalize provider output JSON into a name-to-value mapping.

    Args:
        provider: ``aws`` for a CloudFormation output array or ``azure`` for an
            ARM output object.
        outputs_file: UTF-8 JSON file written by the provider CLI.

    Returns:
        Deployment output names mapped to their string values.

    Raises:
        ValueError: The AWS payload is not an array.
        TypeError: The Azure payload is not an object.
        json.JSONDecodeError: The input file is not valid JSON.
    """
    with outputs_file.open(encoding="utf-8") as input_handle:
        payload: Any = json.load(input_handle)

    if provider == AWS_PROVIDER:
        if not isinstance(payload, list):
            raise ValueError("AWS outputs must be a JSON array.")
        return {
            str(item[AWS_OUTPUT_KEY]): str(item[AWS_OUTPUT_VALUE])
            for item in payload
            if isinstance(item, dict)
            and AWS_OUTPUT_KEY in item
            and AWS_OUTPUT_VALUE in item
        }

    if not isinstance(payload, dict):
        raise TypeError("Azure outputs must be a JSON object.")
    return {
        str(output_name): str(output_data[AZURE_OUTPUT_VALUE])
        for output_name, output_data in payload.items()
        if isinstance(output_data, dict) and AZURE_OUTPUT_VALUE in output_data
    }


def _add_private_key(ssh_command: str, private_key: str) -> str:
    """Insert an optional local identity into a provider-generated SSH command.

    Args:
        ssh_command: Command from the deployment output, expected to start with
            the ``ssh`` executable.
        private_key: Local PEM or private-key path, or an empty string to leave
            the command unchanged.

    Returns:
        A shell-quoted SSH command with ``-i`` inserted when a key was supplied.

    Raises:
        ValueError: The provider output is not an SSH command.
    """
    if not private_key:
        return ssh_command
    command_parts = shlex.split(ssh_command)
    if not command_parts or command_parts[0] != "ssh":
        raise ValueError(f"Unsupported SSH command: {ssh_command}")
    return shlex.join([command_parts[0], "-i", private_key, *command_parts[1:]])


def _required_output(values: dict[str, str], provider: str, logical_name: str) -> str:
    """Resolve a provider-specific output name required by the common guide.

    Args:
        values: Normalized provider output mapping.
        provider: Provider whose physical output names should be used.
        logical_name: Common output role such as ``opamp_url`` or ``server_ssh``.

    Returns:
        The non-empty deployment output value.

    Raises:
        ValueError: The required output is absent or empty.
    """
    provider_name = OUTPUT_NAMES[provider][logical_name]
    value = values.get(provider_name, "").strip()
    if not value:
        raise ValueError(f"Required deployment output is missing: {provider_name}")
    return value


def _render_guide(provider: str, values: dict[str, str], private_key: str) -> str:
    """Render normalized service links and ready-to-run SSH commands.

    Args:
        provider: Provider label used for output-name lookup and the title.
        values: Normalized deployment output mapping.
        private_key: Optional local identity path added to both SSH commands.

    Returns:
        Licensed Markdown suitable for local use and retained object storage.
    """
    opamp_url = _required_output(values, provider, OPAMP_URL_KEY)
    keycloak_url = _required_output(values, provider, KEYCLOAK_URL_KEY)
    server_ssh = _add_private_key(
        _required_output(values, provider, SERVER_SSH_KEY), private_key
    )
    consumer_ssh = _add_private_key(
        _required_output(values, provider, CONSUMER_SSH_KEY), private_key
    )
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    provider_label = provider.upper()
    identity_note = (
        f"Commands include the local identity file `{private_key}`."
        if private_key
        else "Commands use the SSH agent or the platform's default identity file."
    )

    return f"""<!--
Copyright 2026 mp3monster.org
Licensed under the Apache License, Version 2.0.
-->

# {provider_label} deployment connection details

Generated: `{generated_at}`

## Service URLs

- OpAMP server: [{opamp_url}]({opamp_url})
- Keycloak: [{keycloak_url}]({keycloak_url})

The deployment uses self-signed HTTPS certificates, so a browser may require
explicit confirmation before opening these URLs.

## SSH commands

{identity_note}

Server:

```shell
{server_ssh}
```

Consumer:

```shell
{consumer_ssh}
```
"""


def main() -> int:
    """Read outputs, render the guide, and create its destination directory.

    Returns:
        Zero after the Markdown file has been written successfully. Parsing,
        validation, and filesystem errors intentionally propagate to the caller
        so a deploy script cannot mistake incomplete post-processing for success.
    """
    arguments = _parse_arguments()
    output_values = _load_output_values(arguments.provider, arguments.outputs_file)
    guide = _render_guide(arguments.provider, output_values, arguments.ssh_private_key)
    arguments.output_file.parent.mkdir(parents=True, exist_ok=True)
    arguments.output_file.write_text(guide, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
