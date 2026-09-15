#!/usr/bin/env python3
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

"""Consumer launch action builders for the OpAMP CLI.

The CLI does not implement consumer plugins itself. It starts consumer
processes and lets `opamp_consumer.client` route to the selected plugin via
`consumer.service_type`. This module only centralizes the command-line,
environment, process-record, and demo-profile action construction needed by the
CLI guided flows.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from .common import _slugify
    from .constants import (
        ACTION_ID_FLUENTBIT_CLIENT,
        ACTION_ID_FLUENTD_CLIENT,
        ACTION_ID_VECTOR_CLIENT,
        ACTION_KEY_LOG_NAME,
        ACTION_KEY_METADATA,
        ACTION_KEY_RECORD_NAME,
        ARG_AGENT_CONFIG_PATH,
        ARG_CONFIG_PATH,
        LABEL_FLUENTBIT_CLIENT,
        LABEL_FLUENTD_CLIENT,
        LABEL_VECTOR_CLIENT,
        OPAMP_CONFIG_PATH_ENV,
    )
except ImportError:
    from common import _slugify  # type: ignore[no-redef]
    from constants import (  # type: ignore[no-redef]
        ACTION_ID_FLUENTBIT_CLIENT,
        ACTION_ID_FLUENTD_CLIENT,
        ACTION_ID_VECTOR_CLIENT,
        ACTION_KEY_LOG_NAME,
        ACTION_KEY_METADATA,
        ACTION_KEY_RECORD_NAME,
        ARG_AGENT_CONFIG_PATH,
        ARG_CONFIG_PATH,
        LABEL_FLUENTBIT_CLIENT,
        LABEL_FLUENTD_CLIENT,
        LABEL_VECTOR_CLIENT,
        OPAMP_CONFIG_PATH_ENV,
    )

LABEL_ELASTIC_AGENT_CLIENT = "Elastic Agent client"
LABEL_ELASTIC_HEARTBEAT_CLIENT = "Elastic Heartbeat client"
CONSUMER_PYTHON_PATH = Path("consumer/src")
DEFAULT_OPAMP_CONFIG_PATH = Path("config/opamp.json")
MODULE_CONSUMER_GENERIC_CLIENT = "opamp_consumer.client"
MODULE_FLUENTBIT_CLIENT = "opamp_consumer.fluentbit.client"
MODULE_FLUENTD_CLIENT = "opamp_consumer.fluentd.client"


def _consumer_args(
    *,
    config_path: Path,
    agent_config_path: Path | None = None,
) -> list[str]:
    """Return common consumer CLI args.

    `config_path` is always passed because it selects the consumer OpAMP JSON.
    `agent_config_path` is optional and should only be used as an explicit
    profile/default override; new demos should prefer `consumer.agent_config_path`
    inside the JSON config so launch behavior is configuration-driven.
    """
    args = [ARG_CONFIG_PATH, str(config_path)]
    if agent_config_path is not None:
        args.extend([ARG_AGENT_CONFIG_PATH, str(agent_config_path)])
    return args


def _consumer_start_action(
    *,
    repo_root: Path,
    action_id: str,
    label: str,
    module_name: str,
    config_path: Path,
    agent_config_path: Path | None,
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
    record_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    log_name: str | None = None,
) -> dict[str, Any]:
    """Build a consumer background-start action for any supported service.

    `module_name` is the executable Python module. Older direct clients still
    use concrete modules such as `opamp_consumer.fluentbit.client`; plugin-routed
    consumers should use `opamp_consumer.client` so `consumer.service_type`
    controls the actual implementation.
    """
    args = _consumer_args(
        config_path=config_path,
        agent_config_path=agent_config_path,
    )
    env = {OPAMP_CONFIG_PATH_ENV: str(config_path)}
    action = background_start_action(
        action_id=action_id,
        label=label,
        command_text=python_module_command(
            module_name=module_name,
            python_paths=[repo_root / CONSUMER_PYTHON_PATH],
            args=args,
            env=env,
            cwd=repo_root,
        ),
        argv=python_module_argv(module_name=module_name, args=args),
        cwd=repo_root,
        env=build_exec_env(
            python_paths=[repo_root / CONSUMER_PYTHON_PATH],
            env=env,
        ),
        clear_supervisor_signal=True,
    )
    if record_name is not None:
        action[ACTION_KEY_RECORD_NAME] = record_name
    if metadata is not None:
        action[ACTION_KEY_METADATA] = dict(metadata)
    if log_name is not None:
        action[ACTION_KEY_LOG_NAME] = log_name
    return action


def _demo_consumer_start_action(
    *,
    repo_root: Path,
    profile_name: str,
    prefix: str,
    component_key: str,
    label: str,
    module_name: str,
    config_path: Path,
    agent_config_path: Path | None,
    common_metadata: dict[str, Any],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build one demo-profile consumer action.

    The component wrappers below deliberately stay thin. To add another demo
    consumer type, provide its label, stable component key, module name, and
    paths, then let this helper apply the common record metadata and log naming.
    """
    return _consumer_start_action(
        repo_root=repo_root,
        action_id=f"demo_{component_key}_{_slugify(profile_name)}",
        label=f"{label} ({profile_name})",
        module_name=module_name,
        config_path=config_path,
        agent_config_path=agent_config_path,
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
        record_name=f"{prefix}:{label}",
        metadata=common_metadata,
        log_name=f"demo-{_slugify(profile_name)}-{component_key.replace('_', '-')}-client",
    )


def default_fluentbit_start_action(
    *,
    repo_root: Path,
    existing_path: Callable[..., Path | None],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build the default Fluent Bit client start action."""
    opamp_config = (repo_root / DEFAULT_OPAMP_CONFIG_PATH).resolve()
    fluentbit_config = existing_path(
        repo_root / "tests" / "opamp.json",
        opamp_config,
    )
    fluentbit_agent_config = existing_path(
        repo_root / "tests" / "fluent-bit.yaml",
        repo_root / "consumer" / "fluent-bit.yaml",
    )
    return _consumer_start_action(
        repo_root=repo_root,
        action_id=ACTION_ID_FLUENTBIT_CLIENT,
        label=LABEL_FLUENTBIT_CLIENT,
        module_name=MODULE_FLUENTBIT_CLIENT,
        config_path=fluentbit_config or opamp_config,
        agent_config_path=fluentbit_agent_config
        or (repo_root / "consumer" / "fluent-bit.yaml").resolve(),
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )


def default_fluentd_start_action(
    *,
    repo_root: Path,
    existing_path: Callable[..., Path | None],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build the default Fluentd client start action."""
    opamp_config = (repo_root / DEFAULT_OPAMP_CONFIG_PATH).resolve()
    fluentd_config = existing_path(
        repo_root / "consumer" / "opamp-fluentd.json",
        repo_root / "tests" / "opamp.json",
        opamp_config,
    )
    return _consumer_start_action(
        repo_root=repo_root,
        action_id=ACTION_ID_FLUENTD_CLIENT,
        label=LABEL_FLUENTD_CLIENT,
        module_name=MODULE_FLUENTD_CLIENT,
        config_path=fluentd_config or opamp_config,
        agent_config_path=(repo_root / "consumer" / "fluentd.conf").resolve(),
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )


def demo_fluentbit_start_action(
    *,
    repo_root: Path,
    profile_name: str,
    prefix: str,
    config_path: Path,
    agent_config_path: Path | None,
    common_metadata: dict[str, Any],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build a demo-profile Fluent Bit client start action."""
    return _demo_consumer_start_action(
        repo_root=repo_root,
        profile_name=profile_name,
        prefix=prefix,
        component_key="fluentbit",
        label=LABEL_FLUENTBIT_CLIENT,
        module_name=MODULE_FLUENTBIT_CLIENT,
        config_path=config_path,
        agent_config_path=agent_config_path,
        common_metadata=common_metadata,
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )


def demo_fluentd_start_action(
    *,
    repo_root: Path,
    profile_name: str,
    prefix: str,
    config_path: Path,
    agent_config_path: Path | None,
    common_metadata: dict[str, Any],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build a demo-profile Fluentd client start action."""
    return _demo_consumer_start_action(
        repo_root=repo_root,
        profile_name=profile_name,
        prefix=prefix,
        component_key="fluentd",
        label=LABEL_FLUENTD_CLIENT,
        module_name=MODULE_FLUENTD_CLIENT,
        config_path=config_path,
        agent_config_path=agent_config_path,
        common_metadata=common_metadata,
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )


def demo_elastic_agent_start_action(
    *,
    repo_root: Path,
    profile_name: str,
    prefix: str,
    config_path: Path,
    agent_config_path: Path | None,
    common_metadata: dict[str, Any],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build a demo-profile Elastic Agent client start action."""
    return _demo_consumer_start_action(
        repo_root=repo_root,
        profile_name=profile_name,
        prefix=prefix,
        component_key="elastic_agent",
        label=LABEL_ELASTIC_AGENT_CLIENT,
        module_name=MODULE_CONSUMER_GENERIC_CLIENT,
        config_path=config_path,
        agent_config_path=agent_config_path,
        common_metadata=common_metadata,
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )


def demo_elastic_heartbeat_start_action(
    *,
    repo_root: Path,
    profile_name: str,
    prefix: str,
    config_path: Path,
    agent_config_path: Path | None,
    common_metadata: dict[str, Any],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build a demo-profile Elastic Heartbeat client start action."""
    return _demo_consumer_start_action(
        repo_root=repo_root,
        profile_name=profile_name,
        prefix=prefix,
        component_key="elastic_heartbeat",
        label=LABEL_ELASTIC_HEARTBEAT_CLIENT,
        module_name=MODULE_CONSUMER_GENERIC_CLIENT,
        config_path=config_path,
        agent_config_path=agent_config_path,
        common_metadata=common_metadata,
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )


def demo_vector_start_action(
    *,
    repo_root: Path,
    profile_name: str,
    prefix: str,
    config_path: Path,
    agent_config_path: Path | None,
    common_metadata: dict[str, Any],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build a demo-profile Vector client start action."""
    return _demo_consumer_start_action(
        repo_root=repo_root,
        profile_name=profile_name,
        prefix=prefix,
        component_key="vector",
        label=LABEL_VECTOR_CLIENT,
        module_name=MODULE_CONSUMER_GENERIC_CLIENT,
        config_path=config_path,
        agent_config_path=agent_config_path,
        common_metadata=common_metadata,
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )


def default_vector_start_action(
    *,
    repo_root: Path,
    existing_path: Callable[..., Path | None],
    python_module_command: Callable[..., str],
    python_module_argv: Callable[..., list[str]],
    background_start_action: Callable[..., dict[str, Any]],
    build_exec_env: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    """Build the default Vector client start action."""
    vector_config = existing_path(repo_root / "consumer" / "opamp-vector.json")
    vector_agent_config = existing_path(
        repo_root / "docs" / "vector-self-monitor" / "vector-self-monitor.yaml"
    )
    config_path = vector_config or (repo_root / "consumer" / "opamp-vector.json").resolve()
    return _consumer_start_action(
        repo_root=repo_root,
        action_id=ACTION_ID_VECTOR_CLIENT,
        label=LABEL_VECTOR_CLIENT,
        module_name=MODULE_CONSUMER_GENERIC_CLIENT,
        config_path=config_path,
        agent_config_path=vector_agent_config
        or (repo_root / "docs" / "vector-self-monitor" / "vector-self-monitor.yaml").resolve(),
        python_module_command=python_module_command,
        python_module_argv=python_module_argv,
        background_start_action=background_start_action,
        build_exec_env=build_exec_env,
    )
