#!/usr/bin/env python3
"""Containerized startup regression probe for built-in consumer plugins."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

PLUGIN_SPECS = [
    {
        "service_type": "fluentbit",
        "entry_point": "opamp_consumer.fluentbit.client:main",
        "module": "opamp_consumer.fluentbit.client",
        "client_class": "OpAMPClient",
        "agent_filename": "fluent-bit.yaml",
    },
    {
        "service_type": "fluentd",
        "entry_point": "opamp_consumer.fluentd.client:main",
        "module": "opamp_consumer.fluentd.client",
        "client_class": "FluentdOpAMPClient",
        "agent_filename": "fluentd.conf",
    },
    {
        "service_type": "elastic_agent",
        "entry_point": "opamp_consumer.elastic_agent.client:main",
        "module": "opamp_consumer.elastic_agent.client",
        "client_class": "ElasticAgentOpAMPClient",
        "agent_filename": "elastic-agent.yml",
    },
    {
        "service_type": "elastic_heartbeat",
        "entry_point": "opamp_consumer.elastic_heartbeat.client:main",
        "module": "opamp_consumer.elastic_heartbeat.client",
        "client_class": "ElasticHeartbeatOpAMPClient",
        "agent_filename": "heartbeat.yml",
    },
    {
        "service_type": "simulator",
        "entry_point": "opamp_consumer.simulator.client:main",
        "module": "opamp_consumer.simulator.client",
        "client_class": "SimulatorOpAMPClient",
        "agent_filename": "simulator-agent.yaml",
    },
    {
        "service_type": "vector",
        "entry_point": "opamp_consumer.vector.client:main",
        "module": "opamp_consumer.vector.client",
        "client_class": "VectorOpAMPClient",
        "agent_filename": "vector.yaml",
    },
]


def _run(command: list[str], *, cwd: Path) -> None:
    print(f"[consumer-plugin-startup] run: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=str(cwd), check=True)


def _write_agent_configs(work_dir: Path) -> dict[str, Path]:
    configs = {
        "fluent-bit.yaml": (
            "service:\n"
            "  flush: 2\n"
            "  log_level: info\n"
            "  http_server: on\n"
            "  http_listen: 127.0.0.1\n"
            "  http_port: 2020\n"
            "pipeline:\n"
            "  inputs:\n"
            "    - name: dummy\n"
            "      tag: dummy\n"
            "      dummy: '{\"hello\":\"world\"}'\n"
            "  outputs:\n"
            "    - name: stdout\n"
            "      match: '*'\n"
        ),
        "fluentd.conf": (
            "<system>\n"
            "  log_level info\n"
            "</system>\n"
            "<source>\n"
            "  @type monitor_agent\n"
            "  bind 127.0.0.1\n"
            "  port 2020\n"
            "</source>\n"
            "<source>\n"
            "  @type dummy\n"
            "  tag dummy\n"
            "  dummy {\"hello\":\"world\"}\n"
            "</source>\n"
            "<match *>\n"
            "  @type stdout\n"
            "</match>\n"
        ),
        "elastic-agent.yml": (
            "outputs:\n"
            "  default:\n"
            "    type: logstash\n"
            "    hosts: ['127.0.0.1:5044']\n"
            "management:\n"
            "  mode: local\n"
            "inputs: []\n"
            "agent.monitoring:\n"
            "  enabled: true\n"
            "  http:\n"
            "    enabled: true\n"
            "    host: 127.0.0.1\n"
            "    port: 6791\n"
        ),
        "heartbeat.yml": (
            "heartbeat.monitors:\n"
            "  - type: http\n"
            "    id: localhost-http\n"
            "    name: localhost\n"
            "    urls: ['http://localhost']\n"
            "    schedule: '@every 5s'\n"
            "http.enabled: true\n"
            "http.host: 127.0.0.1\n"
            "http.port: 5066\n"
            "output.logstash:\n"
            "  hosts: ['127.0.0.1:5044']\n"
        ),
        "simulator-agent.yaml": "simulator: true\n",
        "vector.yaml": (
            "api:\n"
            "  enabled: true\n"
            "  address: 127.0.0.1:8686\n"
            "sources:\n"
            "  vector_internal_metrics:\n"
            "    type: internal_metrics\n"
            "transforms:\n"
            "  as_logs:\n"
            "    type: metric_to_log\n"
            "    inputs: [vector_internal_metrics]\n"
            "sinks:\n"
            "  out:\n"
            "    type: console\n"
            "    inputs: [as_logs]\n"
            "    encoding:\n"
            "      codec: json\n"
        ),
    }
    paths: dict[str, Path] = {}
    for filename, content in configs.items():
        path = work_dir / filename
        path.write_text(content, encoding="utf-8")
        paths[filename] = path
    return paths


def _write_simulator_responses(work_dir: Path) -> Path:
    path = work_dir / "simulator-responses.json"
    path.write_text(
        json.dumps({"responses": {"*": [{"action": "accept"}]}}, indent=2),
        encoding="utf-8",
    )
    return path


def _consumer_config(
    *,
    service_type: str,
    agent_config_path: Path,
    simulator_responses_path: Path,
    work_dir: Path,
) -> dict[str, Any]:
    consumer: dict[str, Any] = {
        "server_url": "http://127.0.0.1:8080",
        "transport": "http",
        "tls": {"verify_server": False},
        "server-authorization": "none",
        "agent_config_path": str(agent_config_path),
        "agent_additional_params": [],
        "heartbeat_frequency": 30,
        "service_type": service_type,
        "full_update_controller": {"fullResendAfter": 1},
        "full_update_controller_type": "SentCount",
        "log_level": "debug",
        "service_name": service_type,
        "service_namespace": "ConsumerPluginStartupRegression",
        "plugins": [
            {
                "service_type": str(spec["service_type"]),
                "entry_point": str(spec["entry_point"]),
                "enabled": True,
            }
            for spec in PLUGIN_SPECS
        ],
        "elastic_agent": {
            "executable_path": "/bin/true",
            "home_path": str(work_dir / "elastic-agent-home"),
            "api_host": "127.0.0.1",
            "api_port": 6791,
            "api_failon": "degraded",
            "status_timeout_seconds": 1,
        },
        "elastic_heartbeat": {
            "executable_path": "/bin/true",
            "home_path": str(work_dir / "elastic-heartbeat-home"),
            "api_host": "127.0.0.1",
            "api_port": 5066,
            "status_timeout_seconds": 1,
        },
        "vector": {
            "executable_path": "/bin/true",
            "api_host": "127.0.0.1",
            "api_port": 8686,
            "status_timeout_seconds": 1,
        },
    }
    if service_type == "simulator":
        consumer["simulator_responses_path"] = str(simulator_responses_path)
    return {"consumer": consumer}


def _load_config(config_path: Path):
    from opamp_consumer import config as consumer_config

    return consumer_config.load_config_with_overrides(
        config_path=config_path,
        server_url=None,
        server_port=None,
        agent_config_path=None,
        agent_additional_params=None,
        heartbeat_frequency=None,
        log_level=None,
        full_update_controller=None,
    )


def _probe_service(service_type: str, config_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {
        "service_type": service_type,
        "status": "failed",
        "duration_seconds": 0.0,
    }
    try:
        os.environ["OPAMP_CONFIG_PATH"] = str(config_path)
        from opamp_consumer.abstract_client import LOCALHOST_BASE
        from opamp_consumer.client_bootstrap import (
            configure_observability_for_config,
            validate_runtime_server_config,
        )
        from opamp_consumer.plugin_loader import load_consumer_plugin

        config = _load_config(config_path)
        os.environ["APP_ENABLE_DEV_FEATURES"] = "true"
        target = load_consumer_plugin(config)
        module_name = getattr(target, "__module__", "")
        module = importlib.import_module(module_name)

        if service_type == "fluentbit":
            config = module.load_agent_config(config)
            config = validate_runtime_server_config(
                config=config,
                localhost_base=LOCALHOST_BASE,
                missing_status_port_error="client_status_port not found in Fluent Bit config",
            )
            configure_observability_for_config(
                config=config,
                default_service_name="opamp-consumer-fluentbit",
            )
            client = module.OpAMPClient(config.server_url, config)
        elif service_type == "fluentd":
            config = module.load_fluentd_config(config)
            config = validate_runtime_server_config(
                config=config,
                localhost_base=LOCALHOST_BASE,
                missing_status_port_error="client_status_port not found in Fluentd config",
            )
            configure_observability_for_config(
                config=config,
                default_service_name="opamp-consumer-fluentd",
            )
            client = module.FluentdOpAMPClient(config.server_url, config)
        elif service_type == "elastic_agent":
            config = module.load_elastic_agent_config(config)
            config = validate_runtime_server_config(
                config=config,
                localhost_base=LOCALHOST_BASE,
                missing_status_port_error="client_status_port not found for Elastic Agent",
            )
            configure_observability_for_config(
                config=config,
                default_service_name="opamp-consumer-elastic-agent",
            )
            client = module.ElasticAgentOpAMPClient(config.server_url, config)
        elif service_type == "elastic_heartbeat":
            config = module.load_elastic_heartbeat_config(config)
            config = validate_runtime_server_config(
                config=config,
                localhost_base=LOCALHOST_BASE,
                missing_status_port_error="client_status_port not found for Elastic Heartbeat",
            )
            configure_observability_for_config(
                config=config,
                default_service_name="opamp-consumer-elastic-heartbeat",
            )
            client = module.ElasticHeartbeatOpAMPClient(config.server_url, config)
        elif service_type == "simulator":
            if config.client_status_port is None:
                config.client_status_port = 1
            config = validate_runtime_server_config(
                config=config,
                localhost_base=LOCALHOST_BASE,
                missing_status_port_error=(
                    "client_status_port must be set for simulator runtime normalization"
                ),
            )
            configure_observability_for_config(
                config=config,
                default_service_name="opamp-consumer-simulator",
            )
            client = module.SimulatorOpAMPClient(config.server_url, config)
        elif service_type == "vector":
            config = module.load_vector_config(config)
            config = validate_runtime_server_config(
                config=config,
                localhost_base=LOCALHOST_BASE,
                missing_status_port_error="client_status_port not found for Vector",
            )
            configure_observability_for_config(
                config=config,
                default_service_name="opamp-consumer-vector",
            )
            client = module.VectorOpAMPClient(config.server_url, config)
        else:
            raise ValueError(f"unsupported regression service_type: {service_type}")

        result.update(
            {
                "status": "passed",
                "entry_point": f"{module_name}:{getattr(target, '__name__', '<callable>')}",
                "client_class": type(client).__name__,
            }
        )
    except Exception as exc:  # pylint: disable=broad-except
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    finally:
        result["duration_seconds"] = round(time.monotonic() - started, 3)
    return result


def _write_reports(results: list[dict[str, Any]], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": "consumer-plugin-startup",
        "passed": all(result["status"] == "passed" for result in results),
        "results": results,
    }
    (report_dir / "consumer-plugin-startup-results.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Consumer Plugin Startup Regression Results",
        "",
        "| Service type | Status | Entry point | Client class | Duration |",
        "|---|---|---|---|---:|",
    ]
    for result in results:
        lines.append(
            "| {service_type} | {status} | {entry_point} | {client_class} | {duration_seconds}s |".format(
                service_type=result["service_type"],
                status=result["status"],
                entry_point=result.get("entry_point", ""),
                client_class=result.get("client_class", ""),
                duration_seconds=result["duration_seconds"],
            )
        )
    failures = [result for result in results if result["status"] != "passed"]
    if failures:
        lines.extend(["", "## Failures", ""])
        for result in failures:
            lines.append(f"### {result['service_type']}")
            lines.append("")
            lines.append(f"- Error: `{result.get('error', '<unknown>')}`")
            lines.append("")
    (report_dir / "consumer-plugin-startup-results.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--report-dir", type=Path, default=Path("dist/test-reports/consumer-plugin-startup"))
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.install and not args.skip_install:
        _run([sys.executable, "-m", "pip", "install", "-e", str(repo_root / "consumer")], cwd=repo_root)

    src_path = repo_root / "consumer" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    with tempfile.TemporaryDirectory(prefix="opamp-consumer-plugin-startup-") as raw_work_dir:
        work_dir = Path(raw_work_dir)
        agent_configs = _write_agent_configs(work_dir)
        simulator_responses_path = _write_simulator_responses(work_dir)
        results: list[dict[str, Any]] = []
        for spec in PLUGIN_SPECS:
            service_type = str(spec["service_type"])
            config_path = work_dir / f"opamp-{service_type}.json"
            config_path.write_text(
                json.dumps(
                    _consumer_config(
                        service_type=service_type,
                        agent_config_path=agent_configs[str(spec["agent_filename"])],
                        simulator_responses_path=simulator_responses_path,
                        work_dir=work_dir,
                    ),
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            result = _probe_service(service_type, config_path)
            print(
                "[consumer-plugin-startup] "
                f"{result['service_type']}: {result['status']}",
                flush=True,
            )
            results.append(result)

    _write_reports(results, args.report_dir.resolve())
    return 0 if all(result["status"] == "passed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
