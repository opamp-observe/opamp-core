# Copyright 2026 opamp.info
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

"""Subprocess E2E coverage for config-driven consumer plugin routing."""

# ruff: noqa: S101, S603

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from typing import Any


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def _consumer_env(plugin_dir: pathlib.Path, config_path: pathlib.Path) -> dict[str, str]:
    """Build subprocess env for local source imports plus temporary plugins."""
    repo_root = _repo_root()
    env = dict(os.environ)
    env["OPAMP_CONFIG_PATH"] = str(config_path)
    python_paths = [
        str(plugin_dir),
        str(repo_root / "consumer" / "src"),
        str(repo_root),
    ]
    existing_python_path = str(env.get("PYTHONPATH", "")).strip()
    if existing_python_path:
        python_paths.append(existing_python_path)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    return env


def _write_fake_plugin(
    *,
    plugin_dir: pathlib.Path,
    module_name: str,
    marker_path: pathlib.Path,
    marker_value: str,
) -> None:
    """Create a fake consumer plugin module that records execution and exits."""
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / f"{module_name}.py").write_text(
        "\n".join(
            [
                "import pathlib",
                "",
                "CONFIG = None",
                "",
                "def main():",
                "    if CONFIG is None:",
                "        raise RuntimeError('CONFIG was not injected')",
                f"    pathlib.Path({str(marker_path)!r}).write_text(",
                f"        {marker_value!r} + '|' + str(CONFIG.service_type),",
                "        encoding='utf-8',",
                "    )",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _consumer_config(
    *,
    service_type: str,
    plugins: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return minimal consumer config for plugin-router E2E tests."""
    consumer: dict[str, Any] = {
        "server_url": "http://localhost:8080",
        "transport": "http",
        "tls": {"verify_server": False},
        "server-authorization": "none",
        "agent_config_path": "./fake-agent.conf",
        "agent_additional_params": [],
        "heartbeat_frequency": 30,
        "service_type": service_type,
        "full_update_controller": {"fullResendAfter": 1},
        "full_update_controller_type": "SentCount",
        "log_level": "debug",
    }
    if plugins is not None:
        consumer["plugins"] = plugins
    return {"consumer": consumer}


def _run_consumer(
    *,
    config_path: pathlib.Path,
    plugin_dir: pathlib.Path,
) -> subprocess.CompletedProcess[str]:
    """Run the real unified consumer module in a subprocess."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "opamp_consumer.client",
            "--config-path",
            str(config_path),
        ],
        cwd=str(_repo_root()),
        env=_consumer_env(plugin_dir, config_path),
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


def test_client_plugin_e2e_no_configured_plugins_fails(tmp_path: pathlib.Path) -> None:
    """A config with no plugin definitions should not resolve a custom service type."""
    plugin_dir = tmp_path / "plugins"
    config_path = tmp_path / "opamp-no-plugins.json"
    config_path.write_text(
        json.dumps(
            _consumer_config(service_type="missing_configured_plugin"),
            indent=2,
        ),
        encoding="utf-8",
    )

    completed = _run_consumer(config_path=config_path, plugin_dir=plugin_dir)

    assert completed.returncode != 0
    combined_output = completed.stdout + completed.stderr
    assert "unsupported consumer.service_type 'missing_configured_plugin'" in combined_output
    assert (
        "ERROR opamp_consumer.plugin_loader failed to load consumer plugin "
        "service_type=missing_configured_plugin"
    ) in combined_output
    assert "elastic_agent, elastic_heartbeat, fluentbit, fluentd, simulator" in combined_output


def test_client_plugin_e2e_one_configured_plugin_runs(tmp_path: pathlib.Path) -> None:
    """A config with one plugin should load and execute that plugin."""
    plugin_dir = tmp_path / "plugins"
    marker_path = tmp_path / "one-plugin.marker"
    _write_fake_plugin(
        plugin_dir=plugin_dir,
        module_name="one_consumer_plugin",
        marker_path=marker_path,
        marker_value="one",
    )
    config_path = tmp_path / "opamp-one-plugin.json"
    config_path.write_text(
        json.dumps(
            _consumer_config(
                service_type="custom_one",
                plugins=[
                    {
                        "service_type": "custom_one",
                        "entry_point": "one_consumer_plugin:main",
                        "enabled": True,
                    }
                ],
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    completed = _run_consumer(config_path=config_path, plugin_dir=plugin_dir)

    assert completed.returncode == 0, completed.stderr
    combined_output = completed.stdout + completed.stderr
    assert (
        "INFO opamp_consumer.plugin_loader loaded consumer plugin "
        "service_type=custom_one entry_point=one_consumer_plugin:main"
    ) in combined_output
    assert marker_path.read_text(encoding="utf-8") == "one|custom_one"


def test_client_plugin_e2e_all_configured_plugins_routes_selected(
    tmp_path: pathlib.Path,
) -> None:
    """A config with all consumer plugins should route only the selected plugin."""
    plugin_dir = tmp_path / "plugins"
    fluentbit_marker = tmp_path / "fluentbit.marker"
    fluentd_marker = tmp_path / "fluentd.marker"
    elastic_marker = tmp_path / "elastic.marker"
    simulator_marker = tmp_path / "simulator.marker"
    _write_fake_plugin(
        plugin_dir=plugin_dir,
        module_name="fake_fluentbit_plugin",
        marker_path=fluentbit_marker,
        marker_value="fluentbit",
    )
    _write_fake_plugin(
        plugin_dir=plugin_dir,
        module_name="fake_fluentd_plugin",
        marker_path=fluentd_marker,
        marker_value="fluentd",
    )
    _write_fake_plugin(
        plugin_dir=plugin_dir,
        module_name="fake_elastic_plugin",
        marker_path=elastic_marker,
        marker_value="elastic_agent",
    )
    _write_fake_plugin(
        plugin_dir=plugin_dir,
        module_name="fake_simulator_plugin",
        marker_path=simulator_marker,
        marker_value="simulator",
    )
    config_path = tmp_path / "opamp-all-plugins.json"
    config_path.write_text(
        json.dumps(
            _consumer_config(
                service_type="fluentd",
                plugins=[
                    {
                        "service_type": "fluentbit",
                        "entry_point": "fake_fluentbit_plugin:main",
                        "enabled": True,
                    },
                    {
                        "service_type": "fluentd",
                        "entry_point": "fake_fluentd_plugin:main",
                        "enabled": True,
                    },
                    {
                        "service_type": "elastic_agent",
                        "entry_point": "fake_elastic_plugin:main",
                        "enabled": True,
                    },
                    {
                        "service_type": "simulator",
                        "entry_point": "fake_simulator_plugin:main",
                        "enabled": True,
                    },
                ],
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    completed = _run_consumer(config_path=config_path, plugin_dir=plugin_dir)

    assert completed.returncode == 0, completed.stderr
    combined_output = completed.stdout + completed.stderr
    assert (
        "INFO opamp_consumer.plugin_loader loaded consumer plugin "
        "service_type=fluentd entry_point=fake_fluentd_plugin:main"
    ) in combined_output
    assert not fluentbit_marker.exists()
    assert fluentd_marker.read_text(encoding="utf-8") == "fluentd|fluentd"
    assert not elastic_marker.exists()
    assert not simulator_marker.exists()
