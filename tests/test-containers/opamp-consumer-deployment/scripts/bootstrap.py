#!/usr/bin/env python3
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
#
# Copyright 2026 mp3monster.org

"""Bootstrap runtime for the OpAMP consumer deployment test container."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from importlib import metadata
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("/config/test-container.env")
DEFAULTS_DIR = Path("/opt/opamp-test/defaults")
RUNTIME_ROOT = Path("/work/runtime")
STAGED_CONFIG_DIR = RUNTIME_ROOT / "config"
DOWNLOADS_DIR = RUNTIME_ROOT / "downloads"
UNPACKED_WHEEL_DIR = RUNTIME_ROOT / "wheel-unpacked"
ELK_DOWNLOADS_DIR = DOWNLOADS_DIR / "elk"
LOG_GENERATOR_DOWNLOADS_DIR = DOWNLOADS_DIR / "log-generator"

SUPPORTED_DEPLOYMENTS = {
    "elastic_agent",
    "elastic_heartbeat",
    "fluentbit",
    "fluentd",
    "simulator",
    "vector",
}
SUPPORTED_TRANSPORTS = {"http", "websocket"}
CONSUMER_PLUGIN_ENTRY_POINT_GROUP = "opamp_consumer.plugins"
BUILTIN_CONSUMER_PLUGINS = [
    {
        "service_type": "fluentbit",
        "entry_point": "opamp_consumer.fluentbit.client:main",
        "enabled": True,
    },
    {
        "service_type": "fluentd",
        "entry_point": "opamp_consumer.fluentd.client:main",
        "enabled": True,
    },
    {
        "service_type": "elastic_agent",
        "entry_point": "opamp_consumer.elastic_agent.client:main",
        "enabled": True,
    },
    {
        "service_type": "elastic_heartbeat",
        "entry_point": "opamp_consumer.elastic_heartbeat.client:main",
        "enabled": True,
    },
    {
        "service_type": "simulator",
        "entry_point": "opamp_consumer.simulator.client:main",
        "enabled": True,
    },
    {
        "service_type": "vector",
        "entry_point": "opamp_consumer.vector.client:main",
        "enabled": True,
    },
]
SUPPORTED_ELK_COMPONENTS = {
    "elasticsearch": "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-{version}-linux-x86_64.tar.gz",
    "kibana": "https://artifacts.elastic.co/downloads/kibana/kibana-{version}-linux-x86_64.tar.gz",
    "logstash": "https://artifacts.elastic.co/downloads/logstash/logstash-{version}-linux-x86_64.tar.gz",
    "elastic-agent": "https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-{version}-linux-x86_64.tar.gz",
    "fleet-server": "https://artifacts.elastic.co/downloads/fleet-server/fleet-server-{version}-linux-x86_64.tar.gz",
    "heartbeat": "https://artifacts.elastic.co/downloads/beats/heartbeat/heartbeat-{version}-linux-x86_64.tar.gz",
}
ELK_COMPONENT_ALIASES = {
    "elasticagent": "elastic-agent",
    "fleetserver": "fleet-server",
    "elastic-heartbeat": "heartbeat",
    "elasticheartbeat": "heartbeat",
}
DEFAULT_ELK_COMPONENTS = ("elasticsearch", "kibana", "logstash")
DEFAULT_LOG_GENERATOR_REPO = "https://github.com/mingrammer/flog.git"


class ConfigError(RuntimeError):
    """Raised when runtime config is invalid."""


def _log(message: str) -> None:
    print(f"[bootstrap] {message}", flush=True)


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    _log(f"run: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, env=env)


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_csv_list(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_kv_config(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    result: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"invalid line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip().upper()
        if not key:
            raise ConfigError(f"invalid line {line_number}: missing key")
        result[key] = value.strip()
    return result


def _require(cfg: dict[str, str], key: str) -> str:
    value = cfg.get(key)
    if value is None or not value.strip():
        raise ConfigError(f"missing required key: {key}")
    return value.strip()


def _resolve_wheel_path(raw_path: str) -> Path:
    """Resolve WHEEL_PATH from a file, directory, or glob expression."""
    candidate = Path(raw_path)
    if candidate.is_file():
        return candidate
    if candidate.is_dir():
        wheels = sorted(candidate.glob("*.whl"), key=lambda path: path.stat().st_mtime)
        if wheels:
            return wheels[-1]
        raise ConfigError(f"WHEEL_PATH directory contains no wheel files: {candidate}")
    if any(token in raw_path for token in ("*", "?", "[")):
        wheels = sorted(Path().glob(raw_path), key=lambda path: path.stat().st_mtime)
        if wheels:
            return wheels[-1]
    raise ConfigError(f"WHEEL_PATH does not exist or contains no wheel files: {raw_path}")


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _log(f"download: {url} -> {destination}")
    request = urllib.request.Request(url, headers={"User-Agent": "opamp-test-container/1.0"})
    with urllib.request.urlopen(request) as response:  # nosec B310 - controlled URL usage for test tooling
        destination.write_bytes(response.read())


def _select_fluentbit_asset(assets: list[dict[str, Any]]) -> str | None:
    best_score = -10_000
    best_url: str | None = None
    for asset in assets:
        name = str(asset.get("name") or "")
        url = str(asset.get("browser_download_url") or "")
        lower = name.lower()
        if not url:
            continue
        score = 0
        if "linux" in lower:
            score += 30
        if "amd64" in lower or "x86_64" in lower:
            score += 30
        if lower.endswith(".tar.gz"):
            score += 20
        if "debug" in lower:
            score -= 20
        if lower.endswith(".sha256") or lower.endswith(".sig"):
            score -= 200
        if score > best_score:
            best_score = score
            best_url = url
    return best_url


def _install_fluentbit(version: str, cfg: dict[str, str]) -> None:
    explicit_url = cfg.get("FLUENTBIT_DOWNLOAD_URL", "").strip()
    tarball_path = DOWNLOADS_DIR / f"fluent-bit-{version}.tar.gz"

    if explicit_url:
        _download(explicit_url, tarball_path)
    else:
        release_url = f"https://api.github.com/repos/fluent/fluent-bit/releases/tags/v{version}"
        release_json = DOWNLOADS_DIR / f"fluent-bit-release-v{version}.json"
        _download(release_url, release_json)
        release_data = json.loads(release_json.read_text(encoding="utf-8"))
        assets = release_data.get("assets") or []
        asset_url = _select_fluentbit_asset(assets)
        if not asset_url:
            raise ConfigError(
                "unable to resolve a Fluent Bit Linux amd64 release asset. "
                "Set FLUENTBIT_DOWNLOAD_URL explicitly."
            )
        _download(asset_url, tarball_path)

    extract_root = DOWNLOADS_DIR / f"fluent-bit-{version}"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tarball_path, mode="r:gz") as archive:
        archive.extractall(path=extract_root)

    binary_candidates = []
    for path in extract_root.rglob("fluent-bit"):
        if path.is_file():
            binary_candidates.append(path)

    if not binary_candidates:
        raise ConfigError(
            "fluent-bit binary was not found in the downloaded archive. "
            "Set FLUENTBIT_DOWNLOAD_URL to a known binary package."
        )

    source_binary = sorted(binary_candidates, key=lambda p: len(str(p)))[0]
    target_binary = Path("/usr/local/bin/fluent-bit")
    shutil.copy2(source_binary, target_binary)
    target_binary.chmod(target_binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    _run([str(target_binary), "--version"])


def _install_fluentd(version: str) -> None:
    _run(["gem", "install", "fluentd", "--no-document", "-v", version])
    _run(["fluentd", "--version"])


def _install_heartbeat(version: str, cfg: dict[str, str]) -> None:
    explicit_url = cfg.get("HEARTBEAT_DOWNLOAD_URL", "").strip()
    tarball_path = DOWNLOADS_DIR / f"heartbeat-{version}.tar.gz"
    download_url = explicit_url or SUPPORTED_ELK_COMPONENTS["heartbeat"].format(version=version)
    _download(download_url, tarball_path)

    extract_root = DOWNLOADS_DIR / f"heartbeat-{version}"
    _extract_tarball(tarball_path, extract_root)

    binary_candidates = []
    for path in extract_root.rglob("heartbeat"):
        if path.is_file():
            binary_candidates.append(path)

    if not binary_candidates:
        raise ConfigError(
            "heartbeat binary was not found in the downloaded archive. "
            "Set HEARTBEAT_DOWNLOAD_URL to a known Linux x86_64 package."
        )

    source_binary = sorted(binary_candidates, key=lambda p: len(str(p)))[0]
    target_binary = Path("/usr/local/bin/heartbeat")
    shutil.copy2(source_binary, target_binary)
    target_binary.chmod(target_binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    _run([str(target_binary), "version"])


def _extract_tarball(archive_path: Path, target_dir: Path) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:gz") as archive:
        archive.extractall(path=target_dir)


def _resolve_elk_component_name(raw_name: str) -> str:
    normalized = str(raw_name or "").strip().lower()
    if not normalized:
        return ""
    return ELK_COMPONENT_ALIASES.get(normalized, normalized)


def _download_elk_stack_components(cfg: dict[str, str], default_version: str) -> None:
    if not _parse_bool(cfg.get("DOWNLOAD_ELK_COMPONENTS"), default=False):
        return

    elk_version = str(cfg.get("ELK_VERSION", "") or "").strip() or default_version
    if not elk_version:
        raise ConfigError("ELK_VERSION (or AGENT_VERSION) must be provided to download ELK components")

    raw_components = _parse_csv_list(cfg.get("ELK_COMPONENTS"))
    if not raw_components:
        raw_components = list(DEFAULT_ELK_COMPONENTS)

    requested_components = [_resolve_elk_component_name(item) for item in raw_components]
    invalid_components = [item for item in requested_components if item not in SUPPORTED_ELK_COMPONENTS]
    if invalid_components:
        raise ConfigError(
            "ELK_COMPONENTS contains unsupported values: "
            f"{invalid_components}. Supported values: {sorted(SUPPORTED_ELK_COMPONENTS)}"
        )

    extract_components = _parse_bool(cfg.get("EXTRACT_ELK_COMPONENTS"), default=False)
    ELK_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    for component in requested_components:
        override_key = f"{component.upper().replace('-', '_')}_DOWNLOAD_URL"
        explicit_url = str(cfg.get(override_key, "") or "").strip()
        download_url = explicit_url or SUPPORTED_ELK_COMPONENTS[component].format(version=elk_version)
        destination = ELK_DOWNLOADS_DIR / f"{component}-{elk_version}.tar.gz"
        _download(download_url, destination)
        _log(f"downloaded ELK component '{component}' -> {destination}")
        if extract_components:
            extract_dir = ELK_DOWNLOADS_DIR / f"{component}-{elk_version}"
            _extract_tarball(destination, extract_dir)
            _log(f"extracted ELK component '{component}' -> {extract_dir}")


def _download_log_generator(cfg: dict[str, str]) -> None:
    if not _parse_bool(cfg.get("DOWNLOAD_LOG_GENERATOR"), default=False):
        return

    LOG_GENERATOR_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    repo_url = str(cfg.get("LOG_GENERATOR_GITHUB_REPO", "") or "").strip() or DEFAULT_LOG_GENERATOR_REPO
    git_ref = str(cfg.get("LOG_GENERATOR_GIT_REF", "") or "").strip()
    target_dir = LOG_GENERATOR_DOWNLOADS_DIR / "repo"
    if target_dir.exists():
        shutil.rmtree(target_dir)

    clone_command = ["git", "clone", "--depth", "1"]
    if git_ref:
        clone_command.extend(["--branch", git_ref])
    clone_command.extend([repo_url, str(target_dir)])
    _run(clone_command)
    _log(f"downloaded log generator repository -> {target_dir}")

    release_url = str(cfg.get("LOG_GENERATOR_RELEASE_URL", "") or "").strip()
    if release_url:
        release_archive = LOG_GENERATOR_DOWNLOADS_DIR / "release.tar.gz"
        _download(release_url, release_archive)
        release_extract_dir = LOG_GENERATOR_DOWNLOADS_DIR / "release"
        _extract_tarball(release_archive, release_extract_dir)
        _log(f"downloaded log generator release archive -> {release_archive}")
        _log(f"extracted log generator release archive -> {release_extract_dir}")


def _unpack_wheel(wheel_path: Path) -> None:
    if UNPACKED_WHEEL_DIR.exists():
        shutil.rmtree(UNPACKED_WHEEL_DIR)
    UNPACKED_WHEEL_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(wheel_path, "r") as handle:
        handle.extractall(UNPACKED_WHEEL_DIR)
    _log(f"wheel unpacked to {UNPACKED_WHEEL_DIR}")


def _install_consumer_wheel(wheel_path: Path) -> None:
    _unpack_wheel(wheel_path)
    _run([sys.executable, "-m", "pip", "install", "--no-cache-dir", f"{wheel_path}[dev]"])


def _install_consumer_plugin_packages(cfg: dict[str, str]) -> None:
    """Install optional external consumer plugin distributions before verification."""
    for raw_path in _parse_csv_list(cfg.get("CONSUMER_PLUGIN_INSTALLS")):
        plugin_path = Path(raw_path)
        if not plugin_path.exists():
            raise ConfigError(f"CONSUMER_PLUGIN_INSTALLS entry does not exist: {plugin_path}")
        _run([sys.executable, "-m", "pip", "install", "--no-cache-dir", str(plugin_path)])


def _installed_consumer_plugin_entry_points() -> dict[str, str]:
    """Return installed consumer plugin entry points by service type."""
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        candidates = list(entry_points.select(group=CONSUMER_PLUGIN_ENTRY_POINT_GROUP))
    else:
        candidates = list(entry_points.get(CONSUMER_PLUGIN_ENTRY_POINT_GROUP, []))
    return {
        str(entry_point.name).strip().lower(): str(entry_point.value).strip()
        for entry_point in candidates
        if str(entry_point.name).strip()
    }


def _verify_installed_consumer_plugins(*, deployment: str) -> None:
    """Fail fast when expected built-in consumer plugin entry points are unavailable."""
    installed = _installed_consumer_plugin_entry_points()
    expected = {
        str(plugin["service_type"]): str(plugin["entry_point"])
        for plugin in BUILTIN_CONSUMER_PLUGINS
    }
    missing = {
        service_type: entry_point
        for service_type, entry_point in expected.items()
        if installed.get(service_type) != entry_point
    }
    if missing:
        raise ConfigError(
            "missing expected plugin entry points after install: "
            f"{missing}; installed={installed}"
        )
    if deployment not in installed and deployment not in expected:
        raise ConfigError(
            f"DEPLOYMENT_TYPE {deployment!r} is not available in installed consumer plugins"
        )
    _log(f"verified consumer plugin entry points: {sorted(installed)}")


def _ensure_hostname(cfg: dict[str, str]) -> None:
    hostname = cfg.get("HOSTNAME_OVERRIDE", "").strip()
    if not hostname:
        return
    _log(f"requested hostname override: {hostname}")
    subprocess.run(["hostname", hostname], check=False)


def _default_agent_template(deployment: str) -> Path:
    if deployment == "fluentbit":
        return DEFAULTS_DIR / "fluent-bit.yaml"
    if deployment == "elastic_heartbeat":
        return DEFAULTS_DIR / "heartbeat.yml"
    if deployment == "elastic_agent":
        return DEFAULTS_DIR / "elastic-agent.yml"
    if deployment == "vector":
        return DEFAULTS_DIR / "vector.yaml"
    if deployment == "simulator":
        return DEFAULTS_DIR / "simulator-agent.yaml"
    return DEFAULTS_DIR / "fluentd.conf"


def _build_default_consumer_config(
    *,
    deployment: str,
    agent_config_path: Path,
    transport: str,
    http_url: str,
    websocket_url: str,
) -> dict[str, Any]:
    server_url = websocket_url if transport == "websocket" else http_url
    service_name_by_deployment = {
        "fluentbit": "Fluentbit",
        "fluentd": "Fluentd",
        "elastic_heartbeat": "ElasticHeartbeat",
        "elastic_agent": "ElasticAgent",
        "vector": "Vector",
        "simulator": "Simulator",
    }
    heartbeat_frequency = 5 if deployment == "elastic_heartbeat" else 15
    config: dict[str, Any] = {
        "consumer": {
            "server_url": server_url,
            "client_status_port": 2020,
            "chat_ops_port": 8888,
            "transport": transport,
            "tls": {"verify_server": False},
            "server-authorization": "none",
            "log_agent_api_responses": False,
            "agent_config_path": str(agent_config_path),
            "agent_additional_params": [],
            "heartbeat_frequency": heartbeat_frequency,
            "service_type": deployment,
            "full_update_controller": {"fullResendAfter": 1},
            "full_update_controller_type": "SentCount",
            "allow_custom_capabilities": True,
            "log_level": "debug",
            "service_name": service_name_by_deployment.get(deployment, deployment),
            "service_namespace": "TestContainer",
            "plugins": [dict(plugin) for plugin in BUILTIN_CONSUMER_PLUGINS],
        }
    }
    if deployment == "elastic_heartbeat":
        consumer = config["consumer"]
        consumer["client_status_port"] = 5066
        consumer["elastic_heartbeat"] = {
            "executable_path": "heartbeat",
            "api_host": "127.0.0.1",
            "api_port": 5066,
            "status_timeout_seconds": 5,
        }
        consumer["processTracking"] = "Supervisor"
    if deployment == "elastic_agent":
        consumer = config["consumer"]
        consumer["client_status_port"] = 6791
        consumer["elastic_agent"] = {
            "executable_path": "/usr/share/elastic-agent/elastic-agent",
            "home_path": "/usr/share/elastic-agent",
            "api_host": "127.0.0.1",
            "api_port": 6791,
            "api_failon": "failed",
            "status_timeout_seconds": 10,
        }
        consumer["processTracking"] = "Supervisor"
    if deployment == "vector":
        consumer = config["consumer"]
        consumer["client_status_port"] = 8686
        consumer["vector"] = {
            "executable_path": "vector",
            "api_host": "127.0.0.1",
            "api_port": 8686,
            "status_timeout_seconds": 5,
        }
        consumer["processTracking"] = "Supervisor"
    if deployment == "simulator":
        consumer = config["consumer"]
        consumer["simulator_responses_path"] = str(
            DEFAULTS_DIR / "simulator-responses.json"
        )
    return config


def _stage_agent_config(
    *,
    deployment: str,
    cfg: dict[str, str],
    output_dir: Path,
    hostname_override: str | None,
) -> Path:
    agent_filename = {
        "fluentbit": "fluent-bit.yaml",
        "fluentd": "fluentd.conf",
        "elastic_heartbeat": "heartbeat.yml",
        "elastic_agent": "elastic-agent.yml",
        "vector": "vector.yaml",
        "simulator": "simulator-agent.yaml",
    }.get(deployment, "agent.conf")
    staged_path = STAGED_CONFIG_DIR / agent_filename
    source_path_raw = cfg.get("AGENT_CONFIG_PATH", "").strip()

    if source_path_raw:
        source_path = Path(source_path_raw)
        if not source_path.exists():
            raise ConfigError(f"AGENT_CONFIG_PATH does not exist: {source_path}")
        shutil.copy2(source_path, staged_path)
    else:
        template_path = _default_agent_template(deployment)
        template_text = template_path.read_text(encoding="utf-8")
        rendered = template_text.replace("__OUTPUT_DIR__", str(output_dir))
        staged_path.write_text(rendered, encoding="utf-8")

    if hostname_override:
        original = staged_path.read_text(encoding="utf-8")
        annotated = f"# service_instance_id: {hostname_override}\n{original}"
        staged_path.write_text(annotated, encoding="utf-8")

    return staged_path


def _stage_consumer_config(
    *,
    deployment: str,
    cfg: dict[str, str],
    agent_config_path: Path,
    transport: str,
    http_url: str,
    websocket_url: str,
) -> Path:
    staged_path = STAGED_CONFIG_DIR / "opamp-consumer.json"
    source_path_raw = cfg.get("CONSUMER_CONFIG_PATH", "").strip()

    if source_path_raw:
        source_path = Path(source_path_raw)
        if not source_path.exists():
            raise ConfigError(f"CONSUMER_CONFIG_PATH does not exist: {source_path}")
        shutil.copy2(source_path, staged_path)
        data = json.loads(staged_path.read_text(encoding="utf-8"))
    else:
        data = _build_default_consumer_config(
            deployment=deployment,
            agent_config_path=agent_config_path,
            transport=transport,
            http_url=http_url,
            websocket_url=websocket_url,
        )

    consumer = data.setdefault("consumer", {})
    consumer["service_type"] = deployment
    consumer["agent_config_path"] = str(agent_config_path)
    consumer["transport"] = transport

    explicit_server_url = cfg.get("SERVER_URL", "").strip()
    if explicit_server_url:
        consumer["server_url"] = explicit_server_url
    elif transport == "websocket":
        consumer["server_url"] = websocket_url
    else:
        consumer["server_url"] = http_url

    service_name_override = cfg.get("SERVICE_NAME_OVERRIDE", "").strip()
    if service_name_override:
        consumer["service_name"] = service_name_override

    service_namespace_override = cfg.get("SERVICE_NAMESPACE_OVERRIDE", "").strip()
    if service_namespace_override:
        consumer["service_namespace"] = service_namespace_override

    if deployment == "elastic_agent":
        consumer["elastic_agent"] = {
            "executable_path": "/usr/share/elastic-agent/elastic-agent",
            "home_path": "/usr/share/elastic-agent",
            "api_host": "127.0.0.1",
            "api_port": 6791,
            "api_failon": "failed",
            "status_timeout_seconds": 10,
        }
        consumer["processTracking"] = "Supervisor"

    if deployment == "simulator":
        simulator_responses_path = cfg.get(
            "SIMULATOR_RESPONSES_PATH",
            str(DEFAULTS_DIR / "simulator-responses.json"),
        ).strip()
        consumer["simulator_responses_path"] = simulator_responses_path

    service_instance_id_override = cfg.get(
        "SERVICE_INSTANCE_ID_OVERRIDE", ""
    ).strip()
    if service_instance_id_override:
        consumer["service_instance_id"] = service_instance_id_override

    staged_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return staged_path


def _launch_agent_only(deployment: str, agent_config_path: Path, output_dir: Path) -> None:
    log_name = {
        "fluentbit": "fluent-bit-agent.log",
        "fluentd": "fluentd-agent.log",
        "elastic_heartbeat": "heartbeat-agent.log",
    }.get(deployment, "agent.log")
    log_path = output_dir / log_name
    if deployment == "fluentbit":
        command = ["fluent-bit", "-c", str(agent_config_path)]
    elif deployment == "elastic_heartbeat":
        command = ["heartbeat", "-e", "-c", str(agent_config_path)]
    else:
        command = ["fluentd", "-c", str(agent_config_path), "--no-supervisor"]
    _log(f"agent-only mode enabled; logging to {log_path}")
    with log_path.open("a", encoding="utf-8") as handle:
        process = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT)
        process.wait()
        sys.exit(process.returncode)


def _launch_consumer(deployment: str, consumer_config_path: Path, agent_config_path: Path, output_dir: Path) -> None:
    log_name = {
        "fluentbit": "opamp-consumer-fluentbit.log",
        "fluentd": "opamp-consumer-fluentd.log",
        "elastic_heartbeat": "opamp-consumer-elastic-heartbeat.log",
        "elastic_agent": "opamp-consumer-elastic-agent.log",
        "vector": "opamp-consumer-vector.log",
        "simulator": "opamp-consumer-simulator.log",
    }.get(deployment, "opamp-consumer.log")
    log_path = output_dir / log_name
    command = [
        "opamp-consumer",
        "--config-path",
        str(consumer_config_path),
        "--agent-config-path",
        str(agent_config_path),
    ]
    process_environment = os.environ.copy()
    process_environment["OPAMP_CONFIG_PATH"] = str(consumer_config_path)
    _log(f"launching opamp-consumer; logging to {log_path}")
    with log_path.open("a", encoding="utf-8") as handle:
        process = subprocess.Popen(
            command,
            stdout=handle,
            stderr=subprocess.STDOUT,
            env=process_environment,
        )
        process.wait()
        sys.exit(process.returncode)


def main() -> int:
    config_path = Path(os.environ.get("TEST_CONTAINER_CONFIG", str(DEFAULT_CONFIG_PATH)))
    cfg = _load_kv_config(config_path)

    deployment = cfg.get("DEPLOYMENT_TYPE", "fluentbit").strip().lower()
    if deployment not in SUPPORTED_DEPLOYMENTS:
        raise ConfigError(f"DEPLOYMENT_TYPE must be one of: {sorted(SUPPORTED_DEPLOYMENTS)}")

    agent_version = _require(cfg, "AGENT_VERSION")
    transport = cfg.get("CONSUMER_TRANSPORT", "http").strip().lower()
    if transport not in SUPPORTED_TRANSPORTS:
        raise ConfigError(f"CONSUMER_TRANSPORT must be one of: {sorted(SUPPORTED_TRANSPORTS)}")

    agent_only = _parse_bool(cfg.get("AGENT_ONLY"), default=False)
    smoke_only = _parse_bool(cfg.get("SMOKE_ONLY"), default=False)
    skip_agent_install = _parse_bool(cfg.get("SKIP_AGENT_INSTALL"), default=False)

    output_dir = Path(cfg.get("OUTPUT_HOST_DIR", "/host-output").strip())
    output_dir.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    STAGED_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ELK_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_GENERATOR_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    http_url = cfg.get("OPAMP_HTTP_URL", "http://host.docker.internal:8080").strip()
    websocket_url = cfg.get("OPAMP_WEBSOCKET_URL", "ws://host.docker.internal:4320").strip()

    _ensure_hostname(cfg)

    wheel_path = _resolve_wheel_path(_require(cfg, "WHEEL_PATH"))
    _install_consumer_wheel(wheel_path)
    _install_consumer_plugin_packages(cfg)
    _verify_installed_consumer_plugins(deployment=deployment)

    _download_elk_stack_components(cfg, agent_version)
    _download_log_generator(cfg)

    if skip_agent_install:
        _log("agent installation skipped by SKIP_AGENT_INSTALL=true")
    elif deployment == "fluentbit":
        _install_fluentbit(agent_version, cfg)
    elif deployment == "elastic_heartbeat":
        _install_heartbeat(agent_version, cfg)
    elif deployment in {"elastic_agent", "simulator", "vector"}:
        raise ConfigError(
            f"{deployment} installation requires SKIP_AGENT_INSTALL=true"
        )
    else:
        _install_fluentd(agent_version)

    hostname_override = cfg.get("HOSTNAME_OVERRIDE", "").strip() or None
    if cfg.get("APP_ENABLE_DEV_FEATURES", "").strip():
        os.environ["APP_ENABLE_DEV_FEATURES"] = cfg["APP_ENABLE_DEV_FEATURES"].strip()
    staged_agent_path = _stage_agent_config(
        deployment=deployment,
        cfg=cfg,
        output_dir=output_dir,
        hostname_override=hostname_override,
    )

    staged_consumer_path = _stage_consumer_config(
        deployment=deployment,
        cfg=cfg,
        agent_config_path=staged_agent_path,
        transport=transport,
        http_url=http_url,
        websocket_url=websocket_url,
    )

    _log(f"staged agent config: {staged_agent_path}")
    _log(f"staged consumer config: {staged_consumer_path}")
    _log(f"output directory: {output_dir}")

    if smoke_only:
        _log("smoke-only mode enabled; skipping long-running agent/consumer launch")
        return 0

    if agent_only:
        _launch_agent_only(deployment, staged_agent_path, output_dir)
    _launch_consumer(deployment, staged_consumer_path, staged_agent_path, output_dir)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigError as error:
        _log(f"configuration error: {error}")
        raise SystemExit(2)
