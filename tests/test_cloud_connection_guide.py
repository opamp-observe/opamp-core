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

"""Tests for generated cloud deployment connection guides."""

import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPOSITORY_ROOT / "scripts" / "generate_cloud_connection_guide.py"

AWS_OUTPUT_KEY = "OutputKey"
AWS_OUTPUT_VALUE = "OutputValue"
AZURE_TYPE_KEY = "type"
AZURE_VALUE_KEY = "value"
AWS_CONSUMER_SSH_OUTPUT = "ConsumerSsh"
AWS_KEYCLOAK_URL_OUTPUT = "KeycloakUrl"
AWS_OPAMP_URL_OUTPUT = "OpampUiUrl"
AWS_SERVER_SSH_OUTPUT = "ServerSsh"
AZURE_CONSUMER_SSH_OUTPUT = "consumerSsh"
AZURE_KEYCLOAK_URL_OUTPUT = "keycloakUrl"
AZURE_OPAMP_URL_OUTPUT = "opampUiUrl"
AZURE_SERVER_SSH_OUTPUT = "serverSsh"


def _run_generator(
    temporary_path: Path,
    provider: str,
    payload: object,
    private_key: str = "",
) -> str:
    """Run the guide generator with one provider payload and return Markdown."""
    outputs_file = temporary_path / f"{provider}_outputs.json"
    guide_file = temporary_path / f"{provider}_connection_details.md"
    outputs_file.write_text(json.dumps(payload), encoding="utf-8")
    command = [
        sys.executable,
        str(GENERATOR_PATH),
        "--provider",
        provider,
        "--outputs-file",
        str(outputs_file),
        "--output-file",
        str(guide_file),
    ]
    if private_key:
        command.extend(("--ssh-private-key", private_key))
    subprocess.run(command, check=True)
    return guide_file.read_text(encoding="utf-8")


def test_aws_guide_contains_urls_and_keyed_ssh_commands(tmp_path: Path) -> None:
    """Convert CloudFormation's output array into an immediately useful guide."""
    output_values = {
        AWS_OPAMP_URL_OUTPUT: "https://198.51.100.10/",
        AWS_KEYCLOAK_URL_OUTPUT: "https://198.51.100.10:8443/",
        AWS_SERVER_SSH_OUTPUT: "ssh ubuntu@198.51.100.10",
        AWS_CONSUMER_SSH_OUTPUT: "ssh ubuntu@consumer.example.test",
    }
    payload = [
        {AWS_OUTPUT_KEY: output_name, AWS_OUTPUT_VALUE: output_value}
        for output_name, output_value in output_values.items()
    ]

    guide = _run_generator(
        tmp_path,
        "aws",
        payload,
        private_key="C:\\keys\\opamp.pem",
    )

    assert "[https://198.51.100.10/](https://198.51.100.10/)" in guide
    assert "ssh -i 'C:\\keys\\opamp.pem' ubuntu@198.51.100.10" in guide
    assert "ssh -i 'C:\\keys\\opamp.pem' ubuntu@consumer.example.test" in guide


def test_azure_guide_contains_urls_and_default_ssh_commands(tmp_path: Path) -> None:
    """Convert ARM's output object without inventing an unknown identity path."""
    payload = {
        AZURE_OPAMP_URL_OUTPUT: {
            AZURE_TYPE_KEY: "String",
            AZURE_VALUE_KEY: "https://server.test/",
        },
        AZURE_KEYCLOAK_URL_OUTPUT: {
            AZURE_TYPE_KEY: "String",
            AZURE_VALUE_KEY: "https://server.test:8443/",
        },
        AZURE_SERVER_SSH_OUTPUT: {
            AZURE_TYPE_KEY: "String",
            AZURE_VALUE_KEY: "ssh azureuser@server.test",
        },
        AZURE_CONSUMER_SSH_OUTPUT: {
            AZURE_TYPE_KEY: "String",
            AZURE_VALUE_KEY: "ssh azureuser@consumer.test",
        },
    }

    guide = _run_generator(tmp_path, "azure", payload)

    assert "[https://server.test/](https://server.test/)" in guide
    assert "ssh azureuser@server.test" in guide
    assert "ssh azureuser@consumer.test" in guide
    assert "SSH agent" in guide
