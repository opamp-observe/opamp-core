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

"""Menu-driven MCP client configuration utility.

This tool builds MCP client entries for Claude Desktop, Codex, VS Code,
LibreChat, and Gemini CLI from a JSON defaults file. Target handlers are kept
small and registered in one map so new MCP clients can be added without
rewriting the deployment model.
"""

from __future__ import annotations

import argparse
import importlib.resources
import json
import os
import platform
import shutil
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from opamp_mcp_config.targets import (  # noqa: E402
    ApplyResult,
    ClaudeTarget,
    ClientTarget,
    CodexTarget,
    GeminiTarget,
    LibreChatTarget,
    VSCodeTarget,
)

DEFAULT_CONFIG_FILENAME = "mcp-client-defaults.json"
JSON_INDENT = 2
SUPPORTED_CLIENTS = ("claude", "codex", "vscode", "librechat", "gemini")
LEGACY_SERVER_NAMES = ("OpAMP Server", "opamp-server", "opampServer")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _mcp_dir() -> Path:
    return Path(__file__).resolve().parent


def _default_config_path() -> Path:
    return _mcp_dir() / DEFAULT_CONFIG_FILENAME


def _cli_dev_tool_default_settings() -> dict[str, Any]:
    """Return the current defaults used to seed CLI-driven MCP prompts."""
    return deepcopy(_load_json(_default_config_path()))


def cli_dev_tool_spec() -> dict[str, Any]:
    """Return self-described MCP CLI prompt metadata for the OpAMP CLI."""
    settings = _cli_dev_tool_default_settings()
    enabled_clients = ",".join(_enabled_clients(settings))
    server = dict(settings.get("server", {}))
    deployment = dict(settings.get("deployment", {}))
    package_specs = ",".join(
        str(item).strip()
        for item in deployment.get("package_specs", [])
        if str(item).strip()
    )
    return {
        "id": "mcp_client_config",
        "label": "Configure MCP clients",
        "description": (
            "Generate and apply MCP client settings for Claude Desktop, Codex, "
            "VS Code, LibreChat, and Gemini."
        ),
        "script_relpath": "mcp/configure_mcp_clients.py",
        "fixed_args": ["--yes"],
        "arguments": [
            {
                "name": "clients",
                "flag": "--clients",
                "prompt": "Enabled clients, comma-separated",
                "required": True,
                "default": enabled_clients or "claude,codex,vscode",
            },
            {
                "name": "server_host",
                "flag": "--server-host",
                "prompt": "OpAMP provider host",
                "default": str(server.get("host") or "localhost"),
            },
            {
                "name": "server_port",
                "flag": "--server-port",
                "prompt": "OpAMP provider port",
                "default": str(server.get("port") or 8080),
            },
            {
                "name": "deployment_mode",
                "flag": "--deployment-mode",
                "prompt": "Deployment mode",
                "choices": ["source", "package", "python-env"],
                "default": str(deployment.get("mode") or "source"),
            },
            {
                "name": "package_specs",
                "flag": "--package-spec",
                "prompt": "Package or wheel specs, comma-separated",
                "multiple": True,
                "default": package_specs,
            },
            {
                "name": "preview",
                "prompt": "Preview only",
                "kind": "bool",
                "default": False,
                "args_when_true": ["--preview"],
            },
            {
                "name": "dry_run",
                "prompt": "Dry run without writing files",
                "kind": "bool",
                "default": False,
                "args_when_true": ["--dry-run"],
            },
        ],
    }


def _load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif path.name == DEFAULT_CONFIG_FILENAME:
        try:
            defaults = importlib.resources.files("opamp_mcp_config").joinpath(
                DEFAULT_CONFIG_FILENAME
            )
            payload = json.loads(defaults.read_text(encoding="utf-8"))
        except (FileNotFoundError, ModuleNotFoundError):
            raise FileNotFoundError(f"config file not found: {path}") from None
    else:
        raise FileNotFoundError(f"config file not found: {path}")
    if not isinstance(payload, dict):
        raise ValueError(f"config root must be a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=JSON_INDENT) + "\n", encoding="utf-8")


def _resolve_path(raw_path: str, *, base: Path | None = None) -> Path:
    path = Path(str(raw_path or "").strip()).expanduser()
    if path.is_absolute():
        return path.resolve()
    return ((base or _repo_root()) / path).resolve()


def _path_or_default(raw_path: str, default_path: Path) -> Path:
    return _resolve_path(raw_path) if str(raw_path or "").strip() else default_path


def _claude_config_path() -> Path:
    system = platform.system().lower()
    if system == "windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata).expanduser() / "Claude" / "claude_desktop_config.json"
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    if system == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "Claude" / "claude_desktop_config.json"


def _gemini_config_path() -> Path:
    return Path.home() / ".gemini" / "settings.json"


def _server_urls(settings: dict[str, Any]) -> dict[str, str]:
    server = dict(settings.get("server", {}))
    scheme = str(server.get("scheme") or "http").strip().rstrip(":/")
    host = str(server.get("host") or "localhost").strip()
    port = int(server.get("port") or 8080)
    sse_path = str(server.get("sse_path") or "/sse").strip()
    if not sse_path.startswith("/"):
        sse_path = "/" + sse_path
    base_url = f"{scheme}://{host}:{port}"
    return {
        "host": host,
        "base_url": base_url,
        "sse_url": f"{base_url}{sse_path}",
    }


def _base_env(settings: dict[str, Any]) -> dict[str, str]:
    urls = _server_urls(settings)
    return {
        "OPAMP_SERVER_IP": urls["host"],
        "OPAMP_SERVER_URL": urls["base_url"],
        "OPAMP_MCP_SSE_URL": urls["sse_url"],
    }


def _deployment_mode(settings: dict[str, Any]) -> str:
    deployment = dict(settings.get("deployment", {}))
    mode = str(deployment.get("mode") or "source").strip().lower()
    if mode not in {"source", "package", "python-env"}:
        raise ValueError("deployment.mode must be one of: source, package, python-env")
    return mode


def _normalize_package_spec(raw_spec: str) -> str:
    package_spec = str(raw_spec or "").strip()
    if not package_spec:
        return ""
    if package_spec.endswith((".whl", ".tar.gz", ".zip")) or "/" in package_spec or "\\" in package_spec:
        return str(_resolve_path(package_spec))
    return package_spec


def _source_pythonpath(settings: dict[str, Any]) -> str:
    deployment = dict(settings.get("deployment", {}))
    paths = deployment.get("pythonpath_paths", [])
    entries = [
        str(_resolve_path(str(item)))
        for item in paths
        if str(item).strip()
    ]
    existing = str(os.environ.get("PYTHONPATH", "")).strip()
    if existing:
        entries.append(existing)
    return os.pathsep.join(dict.fromkeys(entries))


def _runtime_path() -> str:
    entries = [
        item
        for item in str(os.environ.get("PATH", "")).split(os.pathsep)
        if item
    ]
    for executable in ("python", "python3", "uv", "fastmcp", "codex", "node", "npm", "npx"):
        resolved = shutil.which(executable)
        if resolved:
            entries.append(str(Path(resolved).resolve().parent))
    return os.pathsep.join(dict.fromkeys(entries))


def build_stdio_server_entry(settings: dict[str, Any]) -> dict[str, Any]:
    """Build a stdio MCP server entry for local FastMCP execution."""
    deployment = dict(settings.get("deployment", {}))
    mode = _deployment_mode(settings)
    env = _base_env(settings)
    env["PATH"] = _runtime_path()

    if mode == "source":
        project = str(_resolve_path(str(deployment.get("project") or "provider")))
        server_spec = str(
            _resolve_path(str(deployment.get("source_server_spec") or ""))
        )
        args = ["run", "--project", project]
        if bool(deployment.get("with_fastmcp", True)):
            args.extend(["--with", "fastmcp"])
        if bool(deployment.get("with_editable", True)):
            args.extend(["--with-editable", project])
            if bool(deployment.get("include_repo_editable", True)):
                args.extend(["--with-editable", str(_repo_root())])
        pythonpath = _source_pythonpath(settings)
        if pythonpath:
            env["PYTHONPATH"] = pythonpath
        args.extend(["fastmcp", "run", server_spec])
        return {"command": "uv", "args": args, "env": env}

    if mode == "package":
        server_spec = str(
            deployment.get("package_server_spec")
            or "opamp_provider.mcptool.routes:mcpserver"
        )
        package_specs = [
            _normalize_package_spec(str(item))
            for item in deployment.get("package_specs", [])
            if _normalize_package_spec(str(item))
        ]
        args = ["run"]
        if bool(deployment.get("with_fastmcp", True)):
            args.extend(["--with", "fastmcp"])
        for package_spec in package_specs:
            args.extend(["--with", package_spec])
        args.extend(["fastmcp", "run", server_spec])
        return {"command": "uv", "args": args, "env": env}

    server_spec = str(
        deployment.get("package_server_spec")
        or "opamp_provider.mcptool.routes:mcpserver"
    )
    return {"command": "fastmcp", "args": ["run", server_spec], "env": env}


def build_remote_server_entry(settings: dict[str, Any], client_cfg: dict[str, Any]) -> dict[str, Any]:
    """Build an SSE remote MCP entry."""
    urls = _server_urls(settings)
    remote_command = str(client_cfg.get("remote_command") or "mcp-remote").strip()
    if remote_command == "npx":
        args = ["-y", "mcp-remote", urls["sse_url"]]
    else:
        args = [urls["sse_url"]]
    return {
        "command": remote_command,
        "args": args,
        "env": _base_env(settings),
    }


def build_client_entry(settings: dict[str, Any], client_cfg: dict[str, Any]) -> dict[str, Any]:
    transport = str(client_cfg.get("transport") or "stdio").strip().lower()
    if transport == "sse":
        return build_remote_server_entry(settings, client_cfg)
    return build_stdio_server_entry(settings)


def _merge_server_entry(
    *,
    config_path: Path,
    section_name: str,
    server_name: str,
    server_entry: dict[str, Any],
) -> None:
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8").strip()
        payload = json.loads(text) if text else {}
    else:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError(f"config root must be a JSON object: {config_path}")
    section = payload.get(section_name)
    if not isinstance(section, dict):
        section = {}
        payload[section_name] = section
    keep = server_name.lower()
    for legacy_name in LEGACY_SERVER_NAMES:
        if legacy_name.lower() != keep:
            section.pop(legacy_name, None)
    section[server_name] = server_entry
    _write_json(config_path, payload)


def _simple_yaml_scalar(value: Any) -> str:
    text = str(value)
    return json.dumps(text)


def _simple_yaml_dump(payload: dict[str, Any], *, indent: int = 0) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in payload.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_simple_yaml_dump(value, indent=indent + 2))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f"{prefix}  - {_simple_yaml_scalar(item)}")
        else:
            lines.append(f"{prefix}{key}: {_simple_yaml_scalar(value)}")
    return "\n".join(line for line in lines if line != "") + "\n"


def _merge_librechat_yaml(config_path: Path, server_name: str, entry: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        if config_path.exists():
            raise RuntimeError(
                "PyYAML is required to merge an existing LibreChat YAML file. "
                "Install PyYAML or point to a new file."
            )
        _write_text_yaml(config_path, {"mcpServers": {server_name: entry}})
        return

    if config_path.exists():
        text = config_path.read_text(encoding="utf-8").strip()
        payload = yaml.safe_load(text) if text else {}
    else:
        payload = {}
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError(f"LibreChat config root must be a mapping: {config_path}")
    section = payload.get("mcpServers")
    if not isinstance(section, dict):
        section = {}
        payload["mcpServers"] = section
    keep = server_name.lower()
    for legacy_name in LEGACY_SERVER_NAMES:
        if legacy_name.lower() != keep:
            section.pop(legacy_name, None)
    section[server_name] = entry
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_text_yaml(config_path: Path, payload: dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(_simple_yaml_dump(payload), encoding="utf-8")


TARGETS: dict[str, ClientTarget] = {
    "claude": ClaudeTarget(
        path_or_default=_path_or_default,
        claude_config_path=_claude_config_path,
        build_remote_server_entry=build_remote_server_entry,
        merge_server_entry=_merge_server_entry,
    ),
    "codex": CodexTarget(
        build_stdio_server_entry=build_stdio_server_entry,
    ),
    "vscode": VSCodeTarget(
        path_or_default=_path_or_default,
        repo_root=_repo_root,
        build_client_entry=build_client_entry,
        merge_server_entry=_merge_server_entry,
    ),
    "librechat": LibreChatTarget(
        resolve_path=_resolve_path,
        server_urls=_server_urls,
        build_stdio_server_entry=build_stdio_server_entry,
        merge_librechat_yaml=_merge_librechat_yaml,
    ),
    "gemini": GeminiTarget(
        path_or_default=_path_or_default,
        gemini_config_path=_gemini_config_path,
        build_client_entry=build_client_entry,
        merge_server_entry=_merge_server_entry,
    ),
}


def _enabled_clients(settings: dict[str, Any]) -> list[str]:
    clients = dict(settings.get("clients", {}))
    return [
        key
        for key in SUPPORTED_CLIENTS
        if bool(dict(clients.get(key, {})).get("enabled", False))
    ]


def _set_clients(settings: dict[str, Any], raw_clients: str) -> None:
    requested = {
        item.strip().lower()
        for item in raw_clients.split(",")
        if item.strip()
    }
    aliases = {"chatgpt": "codex", "vs": "vscode", "vs-code": "vscode", "vs_code": "vscode"}
    normalized = {aliases.get(item, item) for item in requested}
    unknown = sorted(normalized.difference(SUPPORTED_CLIENTS))
    if unknown:
        raise ValueError(f"unknown clients: {', '.join(unknown)}")
    for key in SUPPORTED_CLIENTS:
        settings["clients"].setdefault(key, {})["enabled"] = key in normalized


def _summary(settings: dict[str, Any]) -> str:
    urls = _server_urls(settings)
    deployment = dict(settings.get("deployment", {}))
    lines = [
        "Current MCP setup:",
        f"- Clients: {', '.join(_enabled_clients(settings)) or '(none)'}",
        f"- Provider URL: {urls['base_url']}",
        f"- Provider SSE URL: {urls['sse_url']}",
        f"- Deployment mode: {_deployment_mode(settings)}",
    ]
    if _deployment_mode(settings) == "package":
        lines.append(f"- Package specs: {', '.join(deployment.get('package_specs', []))}")
    else:
        lines.append(f"- Project: {_resolve_path(str(deployment.get('project') or 'provider'))}")
    return "\n".join(lines)


def _prompt(raw_prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{raw_prompt}{suffix}: ").strip()
    return value or default


def _prompt_bool(raw_prompt: str, default: bool) -> bool:
    default_text = "y" if default else "n"
    value = _prompt(raw_prompt, default_text).strip().lower()
    return value in {"y", "yes", "true", "1", "on"}


def _edit_clients(settings: dict[str, Any]) -> None:
    clients = ",".join(_enabled_clients(settings))
    _set_clients(settings, _prompt("Enabled clients", clients))


def _edit_server(settings: dict[str, Any]) -> None:
    server = settings.setdefault("server", {})
    server["host"] = _prompt("OpAMP provider host", str(server.get("host") or "localhost"))
    server["port"] = int(_prompt("OpAMP provider port", str(server.get("port") or 8080)))
    server["scheme"] = _prompt("OpAMP provider scheme", str(server.get("scheme") or "http"))
    server["sse_path"] = _prompt("MCP SSE path", str(server.get("sse_path") or "/sse"))


def _edit_deployment(settings: dict[str, Any]) -> None:
    deployment = settings.setdefault("deployment", {})
    mode = _prompt("Deployment mode (source/package/python-env)", _deployment_mode(settings))
    deployment["mode"] = mode.strip().lower()
    if deployment["mode"] == "source":
        deployment["project"] = _prompt("Provider project path", str(deployment.get("project") or "provider"))
        deployment["source_server_spec"] = _prompt(
            "FastMCP source server spec",
            str(deployment.get("source_server_spec") or ""),
        )
        deployment["with_editable"] = _prompt_bool(
            "Use editable local installs",
            bool(deployment.get("with_editable", True)),
        )
    elif deployment["mode"] == "package":
        raw_specs = ",".join(str(item) for item in deployment.get("package_specs", []))
        package_specs = _prompt("Package or wheel specs", raw_specs)
        deployment["package_specs"] = [item.strip() for item in package_specs.split(",") if item.strip()]
        deployment["package_server_spec"] = _prompt(
            "FastMCP package server spec",
            str(deployment.get("package_server_spec") or "opamp_provider.mcptool.routes:mcpserver"),
        )


def _edit_client_details(settings: dict[str, Any]) -> None:
    for key in _enabled_clients(settings):
        cfg = settings["clients"].setdefault(key, {})
        print(f"\n{key}:")
        cfg["name"] = _prompt("Server name", str(cfg.get("name") or key))
        if key != "codex":
            cfg["config_path"] = _prompt("Config path (blank for default)", str(cfg.get("config_path") or ""))
        if key in {"librechat", "gemini"}:
            cfg["transport"] = _prompt("Transport (stdio/sse)", str(cfg.get("transport") or "stdio"))


def _apply(settings: dict[str, Any], *, dry_run: bool) -> list[ApplyResult]:
    results: list[ApplyResult] = []
    for key in _enabled_clients(settings):
        target = TARGETS.get(key)
        if target is None:
            raise ValueError(f"client target not implemented: {key}")
        results.append(target.apply(settings, dry_run=dry_run))
    return results


def _preview(settings: dict[str, Any]) -> str:
    preview = {"summary": _summary(settings), "clients": {}}
    for key in _enabled_clients(settings):
        cfg = dict(settings["clients"].get(key, {}))
        if key == "claude":
            entry = build_remote_server_entry(settings, cfg)
        elif key == "librechat" and str(cfg.get("transport") or "stdio") == "sse":
            entry = {"type": "sse", "url": _server_urls(settings)["sse_url"]}
        else:
            entry = build_client_entry(settings, cfg)
        preview["clients"][key] = entry
    return json.dumps(preview, indent=JSON_INDENT)


def _interactive_menu(settings: dict[str, Any]) -> bool:
    while True:
        print("")
        print(_summary(settings))
        print("")
        print("1. Select clients")
        print("2. Edit provider endpoint")
        print("3. Edit deployment mode")
        print("4. Edit client names and paths")
        print("5. Preview generated config")
        print("6. Apply configuration")
        print("q. Quit")
        choice = _prompt("Choose", "6").strip().lower()
        if choice == "1":
            _edit_clients(settings)
        elif choice == "2":
            _edit_server(settings)
        elif choice == "3":
            _edit_deployment(settings)
        elif choice == "4":
            _edit_client_details(settings)
        elif choice == "5":
            print(_preview(settings))
        elif choice == "6":
            return True
        elif choice in {"q", "quit", "exit"}:
            return False
        else:
            print(f"Unknown choice: {choice}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure OpAMP MCP clients from JSON defaults.",
    )
    parser.add_argument("--config", default=str(_default_config_path()), help="defaults JSON path")
    parser.add_argument("--clients", help="comma-separated clients to enable")
    parser.add_argument("--server-host", help="OpAMP provider host")
    parser.add_argument("--server-port", type=int, help="OpAMP provider port")
    parser.add_argument("--deployment-mode", choices=["source", "package", "python-env"])
    parser.add_argument(
        "--package-spec",
        action="append",
        help="pip/uv package spec or wheel path for package deployment mode",
    )
    parser.add_argument("--yes", action="store_true", help="apply without interactive menu")
    parser.add_argument("--dry-run", action="store_true", help="preview actions without writing")
    parser.add_argument("--preview", action="store_true", help="print generated config preview and exit")
    return parser


def _apply_arg_overrides(settings: dict[str, Any], args: argparse.Namespace) -> None:
    if args.clients:
        _set_clients(settings, args.clients)
    if args.server_host:
        settings.setdefault("server", {})["host"] = args.server_host
    if args.server_port:
        settings.setdefault("server", {})["port"] = int(args.server_port)
    if args.deployment_mode:
        settings.setdefault("deployment", {})["mode"] = args.deployment_mode
    if args.package_spec:
        settings.setdefault("deployment", {})["package_specs"] = list(args.package_spec)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    settings = deepcopy(_load_json(Path(args.config).expanduser()))
    _apply_arg_overrides(settings, args)

    if args.preview:
        print(_preview(settings))
        return 0

    should_apply = bool(args.yes)
    if not should_apply:
        should_apply = _interactive_menu(settings)
    if not should_apply:
        return 0

    results = _apply(settings, dry_run=bool(args.dry_run))
    for result in results:
        action = "would update" if args.dry_run else "updated"
        print(f"{result.client}: {action} {result.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
