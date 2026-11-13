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

"""Configuration loader for the OpAMP provider."""

from __future__ import annotations

import json
import logging
import os
import pathlib
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

ROOT_PATH = pathlib.Path(__file__).resolve().parents[3]  # Repository root used for default config path resolution.
SHARED_SOURCE_PATH = ROOT_PATH / "shared" / "src"  # Editable shared-package source directory.
for import_path in (ROOT_PATH, SHARED_SOURCE_PATH):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from shared.opamp_config import UTF8_ENCODING  # noqa: E402,I001 - requires repo-root path adjustment above
from shared.observability import (  # noqa: E402
    ObservabilityConfig,
    load_observability_config_from_payload,
)

ENV_OPAMP_CONFIG_PATH = "OPAMP_CONFIG_PATH"  # Environment variable overriding provider config file location.
CFG_PROVIDER = "provider"  # Top-level JSON section name for provider settings.
CFG_DELAYED_COMMS_SECONDS = "delayed_comms_seconds"  # Provider JSON key for delayed comms threshold.
CFG_SIGNIFICANT_COMMS_SECONDS = "significant_comms_seconds"  # Provider JSON key for significant comms threshold.
CFG_WEBUI_PORT = "webui_port"  # Provider JSON key for web UI listen port.
CFG_MINUTES_KEEP_DISCONNECTED = "minutes_keep_disconnected"  # Provider JSON key for disconnected-client retention window.
CFG_RETRY_AFTER_SECONDS = "retryAfterSeconds"  # Provider JSON key for Retry-After value on throttled responses.
CFG_CLIENT_EVENT_HISTORY_SIZE = "client_event_history_size"  # Provider JSON key for per-client event history length.
CFG_LOG_LEVEL = "log_level"  # Provider JSON key for logging level override.
CFG_DEFAULT_HEARTBEAT_FREQUENCY = "default_heartbeat_frequency"  # Provider JSON key for default client heartbeat interval.
CFG_LATEST_DOCS_URL = "latest_docs_url"  # Provider JSON key for Latest docs redirect URL.
CFG_HUMAN_IN_LOOP_APPROVAL = "human_in_loop_approval"  # Provider JSON key toggling manual agent approval workflow.
CFG_ALLOW_REMOTE_CONFIG = "allow-remote-config"  # Provider JSON key toggling enhanced remote-config UI and queueing support.
CFG_ALLOW_EFFECTIVE_CONFIG = "allow-effective-config"  # Provider JSON key toggling ServerCapabilities.AcceptsEffectiveConfig advertisement.
CFG_ALLOW_CONNECTION_SETTINGS = "allow-connection-settings"  # Provider JSON key toggling ServerCapabilities.OffersConnectionSettings advertisement.
CFG_ALLOW_CONNECTION_SETTINGS_REQUEST = "allow-connection-settings-request"  # Provider JSON key toggling ServerCapabilities.AcceptsConnectionSettingsRequest advertisement.
CFG_ALLOW_MCP = "allow-mcp"  # Provider JSON key toggling Streamable HTTP MCP route exposure at /mcp.
CFG_OPAMP_USE_AUTHORIZATION = "opamp-use-authorization"  # Provider JSON key controlling OpAMP transport bearer authorization mode.
CFG_UI_USE_AUTHORIZATION = "ui-use-authorization"  # Provider JSON key controlling non-OpAMP HTTP/WebSocket bearer authorization mode.
CFG_METRICS = "metrics"  # Provider JSON key for provider metrics settings.
CFG_METRICS_ENABLED = "enabled"  # Provider metrics key toggling Prometheus and graph endpoints.
CFG_METRICS_GRAPH_HISTORY_MINUTES = "graph_history_minutes"  # Provider metrics key controlling retained gauge-series history.
CFG_TLS = "tls"  # Provider JSON key for shared TLS server settings.
CFG_TLS_ENABLED = "enabled"  # Provider TLS key toggling HTTPS/TLS listener mode.
CFG_TLS_CERT_FILE = "cert_file"  # Provider TLS key for server certificate path.
CFG_TLS_KEY_FILE = "key_file"  # Provider TLS key for server private key path.
CFG_TLS_TRUST_ANCHOR_MODE = "trust_anchor_mode"  # Provider TLS key for trust-anchor policy mode.
CFG_STATE_PERSISTENCE = "state_persistence"  # Provider JSON key for runtime state persistence settings.
CFG_STATE_PERSISTENCE_ENABLED = "enabled"  # Provider state persistence key toggling snapshot persistence.
CFG_STATE_FILE_PREFIX = "state_file_prefix"  # Provider state persistence key for snapshot path prefix.
CFG_STATE_RETENTION_COUNT = "retention_count"  # Provider state persistence key for number of retained snapshots.
CFG_STATE_FLUSH_MODE = "flush_mode"  # Provider state persistence key for flush strategy.
CFG_STATE_AUTOSAVE_INTERVAL = (
    "autosave_interval_seconds_since_change"
)  # Provider state persistence key for autosave interval in seconds.

DEFAULT_DELAYED_COMMS_SECONDS = 60  # Default delayed comms threshold in seconds.
DEFAULT_SIGNIFICANT_COMMS_SECONDS = 300  # Default significant comms threshold in seconds.
DEFAULT_WEBUI_PORT = 8080  # Default web UI listening port.
DEFAULT_MINUTES_KEEP_DISCONNECTED = 30  # Default retention window for disconnected clients in minutes.
DEFAULT_RETRY_AFTER_SECONDS = 30  # Default Retry-After duration in seconds.
DEFAULT_CLIENT_EVENT_HISTORY_SIZE = 50  # Default maximum number of retained client events.
DEFAULT_LOG_LEVEL = "INFO"  # Default provider log level.
DEFAULT_DEFAULT_HEARTBEAT_FREQUENCY = 30  # Default heartbeat frequency assigned to new clients.
DEFAULT_LATEST_DOCS_URL = "https://htmlpreview.github.io/?https://raw.githubusercontent.com/opamp-observe/opamp-core/main/github-landingpage/index.html"  # Default redirect target for /doc-set.
DEFAULT_HUMAN_IN_LOOP_APPROVAL = False  # Default behavior leaves human approval workflow disabled.
DEFAULT_ALLOW_REMOTE_CONFIG = True  # Default behavior enables remote-config UI and related provider flows.
DEFAULT_ALLOW_EFFECTIVE_CONFIG = True  # Default behavior advertises acceptance of effective-config reports.
DEFAULT_ALLOW_CONNECTION_SETTINGS = False  # Default behavior does not advertise connection-settings offers.
DEFAULT_ALLOW_CONNECTION_SETTINGS_REQUEST = False  # Default behavior does not advertise connection-settings requests.
DEFAULT_ALLOW_MCP = False  # Default behavior leaves /mcp disabled unless explicitly enabled.
OPAMP_USE_AUTHORIZATION_NONE = "none"  # Disable OpAMP endpoint bearer auth checks.
OPAMP_USE_AUTHORIZATION_CONFIG_TOKEN = (
    "config-token"  # noqa: S105 - authorization mode label, not a credential.
)
OPAMP_USE_AUTHORIZATION_IDP = (
    "idp"  # Validate OpAMP bearer token via IdP JWT verification settings.
)
DEFAULT_OPAMP_USE_AUTHORIZATION = OPAMP_USE_AUTHORIZATION_NONE  # Default OpAMP auth mode.
DEFAULT_UI_USE_AUTHORIZATION = OPAMP_USE_AUTHORIZATION_NONE  # Default non-OpAMP auth mode.
DEFAULT_METRICS_ENABLED = True  # Default behavior exposes provider metrics unless explicitly disabled.
DEFAULT_METRICS_GRAPH_HISTORY_MINUTES = 0  # Default behavior does not retain gauge history for internal graphs.
DEFAULT_TLS_ENABLED = True  # Default TLS enabled state when provider.tls section is present.
TLS_TRUST_ANCHOR_PARTIAL_CHAIN = "partial_chain"  # Trust-anchor mode allowing intermediate anchors.
TLS_TRUST_ANCHOR_FULL_CHAIN_TO_ROOT = "full_chain_to_root"  # Trust-anchor mode requiring root anchors.
TLS_TRUST_ANCHOR_NONE = "none"  # Trust-anchor mode for local self-signed development without CA-anchor checks.
DEFAULT_TLS_TRUST_ANCHOR_MODE = TLS_TRUST_ANCHOR_FULL_CHAIN_TO_ROOT  # Default provider trust-anchor mode.
DEFAULT_STATE_PERSISTENCE_ENABLED = False  # Default persistence behavior remains in-memory only.
DEFAULT_STATE_FILE_PREFIX = "runtime/opamp_server_state"  # Default snapshot file prefix.
DEFAULT_STATE_RETENTION_COUNT = 5  # Default retained snapshot count.
DEFAULT_STATE_FLUSH_MODE = "graceful_shutdown"  # Default persistence flush mode.
DEFAULT_STATE_AUTOSAVE_INTERVAL = 600  # Default autosave interval in seconds.


@dataclass(frozen=True)
class ProviderTLSConfig:
    """Describe the certificate material used by the provider TLS listener.

    Attributes:
        cert_file: Path to the PEM-encoded server certificate chain.
        key_file: Path to the PEM-encoded private key for ``cert_file``.
        trust_anchor_mode: Certificate-chain validation policy. Supported values are
            ``none``, ``partial_chain``, and ``full_chain_to_root``.
    """

    cert_file: str
    key_file: str
    trust_anchor_mode: str = DEFAULT_TLS_TRUST_ANCHOR_MODE


@dataclass(frozen=True)
class ProviderStatePersistenceConfig:
    """Describe how provider runtime state snapshots are stored and retained.

    Attributes:
        enabled: Whether runtime state snapshots are written to disk.
        state_file_prefix: Path prefix used to construct snapshot filenames.
        retention_count: Maximum number of completed snapshots to retain.
        flush_mode: Strategy that determines when pending state is flushed.
        autosave_interval_seconds_since_change: Minimum changed-state age, in seconds,
            before the autosave process writes a snapshot.
    """

    enabled: bool = DEFAULT_STATE_PERSISTENCE_ENABLED
    state_file_prefix: str = DEFAULT_STATE_FILE_PREFIX
    retention_count: int = DEFAULT_STATE_RETENTION_COUNT
    flush_mode: str = DEFAULT_STATE_FLUSH_MODE
    autosave_interval_seconds_since_change: int = DEFAULT_STATE_AUTOSAVE_INTERVAL


@dataclass(frozen=True)
class ProviderMetricsConfig:
    """Describe provider metrics exposure and in-memory graph retention.

    Attributes:
        enabled: Whether Prometheus and provider graph endpoints are available.
        graph_history_minutes: Number of minutes of gauge samples retained for graphs;
            zero disables graph history retention.
    """

    enabled: bool = DEFAULT_METRICS_ENABLED
    graph_history_minutes: int = DEFAULT_METRICS_GRAPH_HISTORY_MINUTES


@dataclass(frozen=True)
class ProviderConfig:
    """Hold the provider's validated, immutable runtime configuration.

    The immutable object gives provider subsystems a consistent configuration snapshot.
    Update helpers replace the module-level instance instead of mutating fields in place.

    Attributes:
        delayed_comms_seconds: Silence duration that marks client communication as delayed.
        significant_comms_seconds: Silence duration considered a significant outage.
        webui_port: TCP port used by the provider HTTP and browser UI listener.
        minutes_keep_disconnected: Minutes disconnected clients remain in provider state.
        retry_after_seconds: Retry delay advertised when the provider throttles a request.
        client_event_history_size: Maximum event records retained for each client.
        log_level: Provider logging level name, such as ``DEBUG`` or ``INFO``.
        default_heartbeat_frequency: Default heartbeat interval assigned to clients, in seconds.
        latest_docs_url: Target URL used by the latest-documentation redirect.
        human_in_loop_approval: Whether new agents require manual approval.
        allow_remote_config: Whether remote-configuration UI and queueing flows are enabled.
        allow_effective_config: Whether effective-configuration reports are accepted.
        allow_connection_settings: Whether connection-setting offers are advertised.
        allow_connection_settings_request: Whether connection-setting requests are accepted.
        allow_mcp: Whether the Streamable HTTP MCP route is exposed.
        opamp_use_authorization: Authorization mode for OpAMP transport endpoints.
        ui_use_authorization: Authorization mode for non-OpAMP HTTP and WebSocket endpoints.
        metrics: Metrics endpoint and graph-history settings.
        tls: TLS listener settings, or ``None`` when TLS is not configured or is disabled.
        state_persistence: Runtime snapshot storage and retention settings.
        observability: Shared logging, tracing, and metrics-export configuration.
    """

    delayed_comms_seconds: int
    significant_comms_seconds: int
    webui_port: int
    minutes_keep_disconnected: int
    retry_after_seconds: int
    client_event_history_size: int
    log_level: str
    default_heartbeat_frequency: int = DEFAULT_DEFAULT_HEARTBEAT_FREQUENCY
    latest_docs_url: str = DEFAULT_LATEST_DOCS_URL
    human_in_loop_approval: bool = DEFAULT_HUMAN_IN_LOOP_APPROVAL
    allow_remote_config: bool = DEFAULT_ALLOW_REMOTE_CONFIG
    allow_effective_config: bool = DEFAULT_ALLOW_EFFECTIVE_CONFIG
    allow_connection_settings: bool = DEFAULT_ALLOW_CONNECTION_SETTINGS
    allow_connection_settings_request: bool = (
        DEFAULT_ALLOW_CONNECTION_SETTINGS_REQUEST
    )
    allow_mcp: bool = DEFAULT_ALLOW_MCP
    opamp_use_authorization: str = DEFAULT_OPAMP_USE_AUTHORIZATION
    ui_use_authorization: str = DEFAULT_UI_USE_AUTHORIZATION
    metrics: ProviderMetricsConfig = field(default_factory=ProviderMetricsConfig)
    tls: ProviderTLSConfig | None = None
    state_persistence: ProviderStatePersistenceConfig = field(
        default_factory=ProviderStatePersistenceConfig
    )
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)


def resolve_log_level(log_level: str | None) -> int:
    """Resolve a configured log-level name to a standard logging level number.

    Unknown or missing names deliberately fall back to ``logging.INFO`` so malformed
    configuration cannot prevent logging initialization.

    Parameters:
        log_level: Case-insensitive logging level name, or ``None`` to use the default.

    Returns:
        Numeric logging level understood by the standard-library logging package.
    """
    normalized_level = str(log_level or DEFAULT_LOG_LEVEL).strip().upper()
    # Use getLevelName() for compatibility with Python 3.10 where
    # getLevelNamesMapping() is not available.
    level = logging.getLevelName(normalized_level)
    if isinstance(level, int):
        return level
    return logging.INFO


def _repo_root() -> pathlib.Path:
    """Return the repository root used to resolve development-time defaults.

    Returns:
        Absolute or source-relative repository root derived when this module was imported.
    """
    return ROOT_PATH


def _ensure_shared_on_path() -> None:
    """Preserve the former shared-import bootstrap API as a compatibility no-op.

    Shared import paths are now installed during module initialization. Keeping this helper
    avoids breaking callers that still invoke it while making the completed setup explicit.

    Returns:
        ``None``; no additional path mutation is required.
    """
    return None


def _config_path() -> pathlib.Path:
    """Resolve the provider configuration path from environment or repository defaults.

    ``OPAMP_CONFIG_PATH`` has precedence so deployments can select a mounted configuration
    file without changing source-controlled defaults.

    Returns:
        Environment-selected path, or ``config/opamp.json`` beneath the repository root.
    """
    path = os.environ.get(ENV_OPAMP_CONFIG_PATH)
    if path:
        return pathlib.Path(path)
    return _repo_root() / "config" / "opamp.json"


def get_effective_config_path(config_path: str | pathlib.Path | None = None) -> pathlib.Path:
    """Return the normalized provider configuration path used for reads and writes.

    Parameters:
        config_path: Explicit path override. When omitted, environment and repository
            defaults are resolved by :func:`_config_path`.

    Returns:
        Expanded, absolute configuration path.
    """
    if config_path is not None:
        return pathlib.Path(config_path).expanduser().resolve()
    return _config_path().expanduser().resolve()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    """Load a required UTF-8 JSON configuration object from disk.

    Parameters:
        path: File containing the JSON configuration payload.

    Returns:
        Parsed top-level JSON object.

    Raises:
        FileNotFoundError: If ``path`` does not identify an existing file.
        json.JSONDecodeError: If the file does not contain valid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    return json.loads(path.read_text(encoding=UTF8_ENCODING))


def _as_bool(value: Any, default: bool) -> bool:
    """Coerce common JSON and environment boolean forms into a Boolean value.

    Parameters:
        value: Candidate value, including Boolean values and common true/false strings.
        default: Value returned when ``value`` is ``None``.

    Returns:
        Parsed Boolean, the supplied default, or normal Python truthiness for other values.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default if value is None else bool(value)


def _normalize_authorization_mode(
    value: Any,
    *,
    cfg_key: str,
    default_mode: str,
) -> str:
    """Normalize an authorization mode and safely reject unsupported configured values.

    Invalid modes are logged and replaced with the caller's default so a typo does not
    accidentally select an undefined authentication path.

    Parameters:
        value: Raw authorization-mode value from provider configuration.
        cfg_key: Configuration key included in validation warning messages.
        default_mode: Supported mode used when the value is absent, blank, or invalid.

    Returns:
        One of ``none``, ``config-token``, or ``idp``.
    """
    if value is None:
        return default_mode
    normalized = str(value).strip().lower()
    if not normalized:
        return default_mode
    if normalized in {
        OPAMP_USE_AUTHORIZATION_NONE,
        OPAMP_USE_AUTHORIZATION_CONFIG_TOKEN,
        OPAMP_USE_AUTHORIZATION_IDP,
    }:
        return normalized
    logging.getLogger(__name__).warning(
        "invalid provider %s value %r; defaulting to %s",
        cfg_key,
        value,
        default_mode,
    )
    return default_mode


def _normalize_trust_anchor_mode(value: Any) -> str:
    """Normalize and validate the provider TLS trust-anchor policy.

    Parameters:
        value: Raw trust-anchor mode, or ``None`` to select the secure default.

    Returns:
        A supported normalized trust-anchor mode.

    Raises:
        ValueError: If a non-empty value is not one of the supported modes.
    """
    if value is None:
        return DEFAULT_TLS_TRUST_ANCHOR_MODE
    normalized = str(value).strip().lower()
    if not normalized:
        return DEFAULT_TLS_TRUST_ANCHOR_MODE
    if normalized in {
        TLS_TRUST_ANCHOR_NONE,
        TLS_TRUST_ANCHOR_PARTIAL_CHAIN,
        TLS_TRUST_ANCHOR_FULL_CHAIN_TO_ROOT,
    }:
        return normalized
    raise ValueError(
        f"{CFG_PROVIDER}.{CFG_TLS}.{CFG_TLS_TRUST_ANCHOR_MODE} has unsupported value "
        f"{value!r}"
    )


def _validate_required_file_path(*, cfg_key: str, value: Any) -> str:
    """Validate that a required configuration value names an existing file.

    Parameters:
        cfg_key: Fully qualified configuration key used in validation errors.
        value: Candidate filesystem path from the configuration payload.

    Returns:
        Stripped path string suitable for the provider TLS configuration.

    Raises:
        ValueError: If the value is blank, missing, or does not identify a file.
    """
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{cfg_key} is required")
    path = pathlib.Path(normalized)
    if not path.exists() or not path.is_file():
        raise ValueError(f"{cfg_key} must reference an existing file")
    return normalized


def _load_provider_tls_config(provider_raw: dict[str, Any]) -> ProviderTLSConfig | None:
    """Load and validate optional provider TLS settings.

    Parameters:
        provider_raw: Provider section from the shared OpAMP configuration object.

    Returns:
        Validated TLS settings, or ``None`` when the section is absent or disabled.

    Raises:
        ValueError: If the TLS section has the wrong shape, required files are invalid, or
            the trust-anchor mode is unsupported.
    """
    tls_raw = provider_raw.get(CFG_TLS)
    if tls_raw is None:
        return None
    if not isinstance(tls_raw, dict):
        raise ValueError(f"{CFG_PROVIDER}.{CFG_TLS} must be an object")
    tls_enabled = _as_bool(tls_raw.get(CFG_TLS_ENABLED), DEFAULT_TLS_ENABLED)
    if not tls_enabled:
        return None
    cert_file = _validate_required_file_path(
        cfg_key=f"{CFG_PROVIDER}.{CFG_TLS}.{CFG_TLS_CERT_FILE}",
        value=tls_raw.get(CFG_TLS_CERT_FILE),
    )
    key_file = _validate_required_file_path(
        cfg_key=f"{CFG_PROVIDER}.{CFG_TLS}.{CFG_TLS_KEY_FILE}",
        value=tls_raw.get(CFG_TLS_KEY_FILE),
    )
    return ProviderTLSConfig(
        cert_file=cert_file,
        key_file=key_file,
        trust_anchor_mode=_normalize_trust_anchor_mode(
            tls_raw.get(CFG_TLS_TRUST_ANCHOR_MODE)
        ),
    )


def _validate_state_persistence_directory(
    *,
    state_file_prefix: str,
) -> tuple[bool, str]:
    """Prepare and validate the directory that will hold provider state snapshots.

    The directory is created when missing because persistence may be enabled before the
    first snapshot exists. Operational failures are returned for controlled startup handling.

    Parameters:
        state_file_prefix: Snapshot filename prefix whose parent directory is validated.

    Returns:
        Pair containing a success flag and either the resolved directory or failure reason.
    """
    prefix_path = pathlib.Path(str(state_file_prefix).strip() or DEFAULT_STATE_FILE_PREFIX)
    directory = prefix_path.parent
    if str(directory).strip() in {"", "."}:
        directory = pathlib.Path.cwd()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return False, f"failed to create state persistence directory {directory}: {exc}"
    if not directory.exists() or not directory.is_dir():
        return False, f"state persistence directory is not a directory: {directory}"
    if not os.access(directory, os.R_OK | os.W_OK):
        return False, f"state persistence directory must be readable and writable: {directory}"
    return True, str(directory)


def _load_state_persistence_config(
    provider_raw: dict[str, Any],
) -> ProviderStatePersistenceConfig:
    """Load provider state-persistence settings and verify their storage directory.

    Persistence is disabled for the current run when its directory cannot be prepared. This
    keeps the provider available while logging the storage problem for the operator.

    Parameters:
        provider_raw: Provider section from the shared OpAMP configuration object.

    Returns:
        Normalized persistence settings, possibly with ``enabled`` forced to ``False`` when
        the configured directory is unusable.

    Raises:
        ValueError: If the persistence section is not an object or numeric values cannot be
            converted to integers.
    """
    raw = provider_raw.get(CFG_STATE_PERSISTENCE)
    if raw is None:
        return ProviderStatePersistenceConfig()
    if not isinstance(raw, dict):
        raise ValueError(f"{CFG_PROVIDER}.{CFG_STATE_PERSISTENCE} must be an object")
    enabled = _as_bool(
        raw.get(CFG_STATE_PERSISTENCE_ENABLED),
        DEFAULT_STATE_PERSISTENCE_ENABLED,
    )
    state_file_prefix = str(
        raw.get(CFG_STATE_FILE_PREFIX, DEFAULT_STATE_FILE_PREFIX) or DEFAULT_STATE_FILE_PREFIX
    ).strip()
    if not state_file_prefix:
        state_file_prefix = DEFAULT_STATE_FILE_PREFIX
    retention_count = max(
        1,
        int(raw.get(CFG_STATE_RETENTION_COUNT, DEFAULT_STATE_RETENTION_COUNT)),
    )
    autosave_interval_seconds_since_change = max(
        1,
        int(raw.get(CFG_STATE_AUTOSAVE_INTERVAL, DEFAULT_STATE_AUTOSAVE_INTERVAL)),
    )
    flush_mode = str(raw.get(CFG_STATE_FLUSH_MODE, DEFAULT_STATE_FLUSH_MODE)).strip()
    if not flush_mode:
        flush_mode = DEFAULT_STATE_FLUSH_MODE
    config = ProviderStatePersistenceConfig(
        enabled=enabled,
        state_file_prefix=state_file_prefix,
        retention_count=retention_count,
        flush_mode=flush_mode,
        autosave_interval_seconds_since_change=autosave_interval_seconds_since_change,
    )
    if not config.enabled:
        return config
    valid, reason = _validate_state_persistence_directory(
        state_file_prefix=config.state_file_prefix
    )
    if valid:
        return config
    logging.getLogger(__name__).error(
        "state persistence disabled for this run: %s",
        reason,
    )
    return ProviderStatePersistenceConfig(
        enabled=False,
        state_file_prefix=config.state_file_prefix,
        retention_count=config.retention_count,
        flush_mode=config.flush_mode,
        autosave_interval_seconds_since_change=config.autosave_interval_seconds_since_change,
    )


def _load_metrics_config(provider_raw: dict[str, Any]) -> ProviderMetricsConfig:
    """Load and normalize provider metrics settings.

    Parameters:
        provider_raw: Provider section from the shared OpAMP configuration object.

    Returns:
        Metrics settings with graph history clamped to a non-negative duration.

    Raises:
        ValueError: If the metrics section is not an object or its history value is not an
            integer-compatible value.
    """
    raw = provider_raw.get(CFG_METRICS)
    if raw is None:
        return ProviderMetricsConfig()
    if not isinstance(raw, dict):
        raise ValueError(f"{CFG_PROVIDER}.{CFG_METRICS} must be an object")
    return ProviderMetricsConfig(
        enabled=_as_bool(
            raw.get(CFG_METRICS_ENABLED),
            DEFAULT_METRICS_ENABLED,
        ),
        graph_history_minutes=max(
            0,
            int(
                raw.get(
                    CFG_METRICS_GRAPH_HISTORY_MINUTES,
                    DEFAULT_METRICS_GRAPH_HISTORY_MINUTES,
                )
            ),
        ),
    )


def load_config() -> ProviderConfig:
    """Load the provider's configured runtime snapshot from the effective JSON file.

    Component settings are read from the provider section while shared observability settings
    are loaded from the complete payload. Defaults are applied for omitted optional values.

    Returns:
        Validated immutable provider configuration.

    Raises:
        FileNotFoundError: If the effective configuration file does not exist.
        json.JSONDecodeError: If the configuration file contains invalid JSON.
        TypeError: If the provider section is not a JSON object.
        ValueError: If a configured value cannot be normalized or validated.
    """
    logging.getLogger(__name__).debug("About to load_config")

    raw = _load_json(_config_path())
    provider_raw = raw.get(CFG_PROVIDER, {})
    observability = load_observability_config_from_payload(raw)
    tls_config = _load_provider_tls_config(provider_raw)
    state_persistence_config = _load_state_persistence_config(provider_raw)
    metrics_config = _load_metrics_config(provider_raw)
    delayed = int(provider_raw.get(CFG_DELAYED_COMMS_SECONDS, DEFAULT_DELAYED_COMMS_SECONDS))
    significant = int(
        provider_raw.get(CFG_SIGNIFICANT_COMMS_SECONDS, DEFAULT_SIGNIFICANT_COMMS_SECONDS)
    )
    opamp_use_authorization_raw = provider_raw.get(CFG_OPAMP_USE_AUTHORIZATION)
    ui_use_authorization_raw = provider_raw.get(CFG_UI_USE_AUTHORIZATION)
    latest_docs_url = str(
        provider_raw.get(CFG_LATEST_DOCS_URL, DEFAULT_LATEST_DOCS_URL)
        or DEFAULT_LATEST_DOCS_URL
    ).strip()
    if not latest_docs_url:
        latest_docs_url = DEFAULT_LATEST_DOCS_URL
    return ProviderConfig(
        delayed_comms_seconds=delayed,
        significant_comms_seconds=significant,
        webui_port=int(provider_raw.get(CFG_WEBUI_PORT, DEFAULT_WEBUI_PORT)),
        minutes_keep_disconnected=int(
            provider_raw.get(CFG_MINUTES_KEEP_DISCONNECTED, DEFAULT_MINUTES_KEEP_DISCONNECTED)
        ),
        retry_after_seconds=int(
            provider_raw.get(CFG_RETRY_AFTER_SECONDS, DEFAULT_RETRY_AFTER_SECONDS)
        ),
        client_event_history_size=max(
            1,
            int(
                provider_raw.get(
                    CFG_CLIENT_EVENT_HISTORY_SIZE, DEFAULT_CLIENT_EVENT_HISTORY_SIZE
                )
            ),
        ),
        log_level=str(provider_raw.get(CFG_LOG_LEVEL, DEFAULT_LOG_LEVEL)),
        default_heartbeat_frequency=max(
            1,
            int(
                provider_raw.get(
                    CFG_DEFAULT_HEARTBEAT_FREQUENCY,
                    DEFAULT_DEFAULT_HEARTBEAT_FREQUENCY,
                )
            ),
        ),
        latest_docs_url=latest_docs_url,
        human_in_loop_approval=_as_bool(
            provider_raw.get(
                CFG_HUMAN_IN_LOOP_APPROVAL,
                DEFAULT_HUMAN_IN_LOOP_APPROVAL,
            ),
            DEFAULT_HUMAN_IN_LOOP_APPROVAL,
        ),
        allow_remote_config=_as_bool(
            provider_raw.get(
                CFG_ALLOW_REMOTE_CONFIG,
                DEFAULT_ALLOW_REMOTE_CONFIG,
            ),
            DEFAULT_ALLOW_REMOTE_CONFIG,
        ),
        allow_effective_config=_as_bool(
            provider_raw.get(
                CFG_ALLOW_EFFECTIVE_CONFIG,
                DEFAULT_ALLOW_EFFECTIVE_CONFIG,
            ),
            DEFAULT_ALLOW_EFFECTIVE_CONFIG,
        ),
        allow_connection_settings=_as_bool(
            provider_raw.get(
                CFG_ALLOW_CONNECTION_SETTINGS,
                DEFAULT_ALLOW_CONNECTION_SETTINGS,
            ),
            DEFAULT_ALLOW_CONNECTION_SETTINGS,
        ),
        allow_connection_settings_request=_as_bool(
            provider_raw.get(
                CFG_ALLOW_CONNECTION_SETTINGS_REQUEST,
                DEFAULT_ALLOW_CONNECTION_SETTINGS_REQUEST,
            ),
            DEFAULT_ALLOW_CONNECTION_SETTINGS_REQUEST,
        ),
        allow_mcp=_as_bool(
            provider_raw.get(
                CFG_ALLOW_MCP,
                DEFAULT_ALLOW_MCP,
            ),
            DEFAULT_ALLOW_MCP,
        ),
        opamp_use_authorization=_normalize_authorization_mode(
            opamp_use_authorization_raw,
            cfg_key=CFG_OPAMP_USE_AUTHORIZATION,
            default_mode=DEFAULT_OPAMP_USE_AUTHORIZATION,
        ),
        ui_use_authorization=_normalize_authorization_mode(
            ui_use_authorization_raw,
            cfg_key=CFG_UI_USE_AUTHORIZATION,
            default_mode=DEFAULT_UI_USE_AUTHORIZATION,
        ),
        metrics=metrics_config,
        tls=tls_config,
        state_persistence=state_persistence_config,
        observability=observability,
    )


def load_config_with_overrides(
    *,
    config_path: pathlib.Path | None,
    log_level: str | None,
) -> ProviderConfig:
    """Load provider configuration and apply explicit command-line overrides.

    The explicit path selects the source file and the explicit log level takes precedence
    over its JSON counterpart. All other settings use the same validation and defaults as
    :func:`load_config`.

    Parameters:
        config_path: Explicit JSON configuration path, or ``None`` to use environment and
            repository defaults.
        log_level: Explicit logging level name, or ``None`` to retain the JSON/default value.

    Returns:
        Validated immutable provider configuration with overrides applied.

    Raises:
        FileNotFoundError: If the selected configuration file does not exist.
        json.JSONDecodeError: If the selected file contains invalid JSON.
        TypeError: If the provider section is not a JSON object.
        ValueError: If a configured value cannot be normalized or validated.
    """
    logging.getLogger(__name__).debug("About to load_config_with_overrides")
    base_raw = _load_json(config_path or _config_path())
    provider_raw = base_raw.get(CFG_PROVIDER, {})
    observability = load_observability_config_from_payload(base_raw)
    tls_config = _load_provider_tls_config(provider_raw)
    state_persistence_config = _load_state_persistence_config(provider_raw)
    metrics_config = _load_metrics_config(provider_raw)
    delayed = int(provider_raw.get(CFG_DELAYED_COMMS_SECONDS, DEFAULT_DELAYED_COMMS_SECONDS))
    significant = int(
        provider_raw.get(CFG_SIGNIFICANT_COMMS_SECONDS, DEFAULT_SIGNIFICANT_COMMS_SECONDS)
    )
    opamp_use_authorization_raw = provider_raw.get(CFG_OPAMP_USE_AUTHORIZATION)
    ui_use_authorization_raw = provider_raw.get(CFG_UI_USE_AUTHORIZATION)
    latest_docs_url = str(
        provider_raw.get(CFG_LATEST_DOCS_URL, DEFAULT_LATEST_DOCS_URL)
        or DEFAULT_LATEST_DOCS_URL
    ).strip()
    if not latest_docs_url:
        latest_docs_url = DEFAULT_LATEST_DOCS_URL
    return ProviderConfig(
        delayed_comms_seconds=delayed,
        significant_comms_seconds=significant,
        webui_port=int(provider_raw.get(CFG_WEBUI_PORT, DEFAULT_WEBUI_PORT)),
        minutes_keep_disconnected=int(
            provider_raw.get(CFG_MINUTES_KEEP_DISCONNECTED, DEFAULT_MINUTES_KEEP_DISCONNECTED)
        ),
        retry_after_seconds=int(
            provider_raw.get(CFG_RETRY_AFTER_SECONDS, DEFAULT_RETRY_AFTER_SECONDS)
        ),
        client_event_history_size=max(
            1,
            int(
                provider_raw.get(
                    CFG_CLIENT_EVENT_HISTORY_SIZE, DEFAULT_CLIENT_EVENT_HISTORY_SIZE
                )
            ),
        ),
        log_level=str(provider_raw.get(CFG_LOG_LEVEL, DEFAULT_LOG_LEVEL))
        if log_level is None
        else str(log_level),
        default_heartbeat_frequency=max(
            1,
            int(
                provider_raw.get(
                    CFG_DEFAULT_HEARTBEAT_FREQUENCY,
                    DEFAULT_DEFAULT_HEARTBEAT_FREQUENCY,
                )
            ),
        ),
        latest_docs_url=latest_docs_url,
        human_in_loop_approval=_as_bool(
            provider_raw.get(
                CFG_HUMAN_IN_LOOP_APPROVAL,
                DEFAULT_HUMAN_IN_LOOP_APPROVAL,
            ),
            DEFAULT_HUMAN_IN_LOOP_APPROVAL,
        ),
        allow_remote_config=_as_bool(
            provider_raw.get(
                CFG_ALLOW_REMOTE_CONFIG,
                DEFAULT_ALLOW_REMOTE_CONFIG,
            ),
            DEFAULT_ALLOW_REMOTE_CONFIG,
        ),
        allow_effective_config=_as_bool(
            provider_raw.get(
                CFG_ALLOW_EFFECTIVE_CONFIG,
                DEFAULT_ALLOW_EFFECTIVE_CONFIG,
            ),
            DEFAULT_ALLOW_EFFECTIVE_CONFIG,
        ),
        allow_connection_settings=_as_bool(
            provider_raw.get(
                CFG_ALLOW_CONNECTION_SETTINGS,
                DEFAULT_ALLOW_CONNECTION_SETTINGS,
            ),
            DEFAULT_ALLOW_CONNECTION_SETTINGS,
        ),
        allow_connection_settings_request=_as_bool(
            provider_raw.get(
                CFG_ALLOW_CONNECTION_SETTINGS_REQUEST,
                DEFAULT_ALLOW_CONNECTION_SETTINGS_REQUEST,
            ),
            DEFAULT_ALLOW_CONNECTION_SETTINGS_REQUEST,
        ),
        allow_mcp=_as_bool(
            provider_raw.get(
                CFG_ALLOW_MCP,
                DEFAULT_ALLOW_MCP,
            ),
            DEFAULT_ALLOW_MCP,
        ),
        opamp_use_authorization=_normalize_authorization_mode(
            opamp_use_authorization_raw,
            cfg_key=CFG_OPAMP_USE_AUTHORIZATION,
            default_mode=DEFAULT_OPAMP_USE_AUTHORIZATION,
        ),
        ui_use_authorization=_normalize_authorization_mode(
            ui_use_authorization_raw,
            cfg_key=CFG_UI_USE_AUTHORIZATION,
            default_mode=DEFAULT_UI_USE_AUTHORIZATION,
        ),
        metrics=metrics_config,
        tls=tls_config,
        state_persistence=state_persistence_config,
        observability=observability,
    )


def set_config(config: ProviderConfig) -> None:
    """Replace the module-level provider configuration snapshot.

    Centralizing replacement ensures runtime update helpers and provider consumers observe
    the same immutable object.

    Parameters:
        config: Fully constructed provider configuration to publish to module consumers.

    Returns:
        ``None``; the module-level ``CONFIG`` reference is updated as a side effect.
    """
    global CONFIG
    CONFIG = config  # Module-level provider config singleton.
    logging.getLogger(__name__).debug("setting config to: \n%s", config)



def update_comms_thresholds(
    *,
    delayed: int,
    significant: int,
    minutes_keep_disconnected: int | None = None,
    client_event_history_size: int | None = None,
    human_in_loop_approval: bool | None = None,
    state_persistence_enabled: bool | None = None,
    state_save_folder: str | None = None,
    retention_count: int | None = None,
    autosave_interval_seconds_since_change: int | None = None,
) -> ProviderConfig:
    """Apply server communication and persistence updates to the active configuration.

    Unspecified optional values are copied from the current immutable configuration. The
    replacement is published through :func:`set_config` so all runtime consumers see it.

    Parameters:
        delayed: Silence threshold, in seconds, for delayed client communication.
        significant: Silence threshold, in seconds, for a significant communication outage.
        minutes_keep_disconnected: Optional disconnected-client retention window in minutes.
        client_event_history_size: Optional maximum retained event count per client.
        human_in_loop_approval: Optional switch for manual agent approval.
        state_persistence_enabled: Optional switch for runtime state snapshots.
        state_save_folder: Optional directory in which the existing snapshot basename is used.
        retention_count: Optional maximum number of snapshots to retain.
        autosave_interval_seconds_since_change: Optional minimum changed-state age before an
            autosave, in seconds.

    Returns:
        Newly published provider configuration snapshot.

    Raises:
        ValueError: If a retention duration, persistence count, autosave interval, or state
            save directory is invalid.
    """
    keep_minutes = (
        CONFIG.minutes_keep_disconnected
        if minutes_keep_disconnected is None
        else int(minutes_keep_disconnected)
    )
    if keep_minutes <= 0:
        raise ValueError("minutes_keep_disconnected must be positive")
    history_size = (
        CONFIG.client_event_history_size
        if client_event_history_size is None
        else max(1, int(client_event_history_size))
    )
    effective_human_in_loop_approval = (
        CONFIG.human_in_loop_approval
        if human_in_loop_approval is None
        else bool(human_in_loop_approval)
    )
    persistence = CONFIG.state_persistence
    if state_persistence_enabled is not None:
        persistence = ProviderStatePersistenceConfig(
            enabled=bool(state_persistence_enabled),
            state_file_prefix=persistence.state_file_prefix,
            retention_count=persistence.retention_count,
            flush_mode=persistence.flush_mode,
            autosave_interval_seconds_since_change=(
                persistence.autosave_interval_seconds_since_change
            ),
        )
    if state_save_folder is not None:
        folder = str(state_save_folder).strip()
        if not folder:
            raise ValueError("state_save_folder must be a non-empty string")
        current_prefix = pathlib.Path(persistence.state_file_prefix)
        base_name = current_prefix.name or "opamp_server_state"
        proposed_prefix = str(pathlib.Path(folder) / base_name)
        valid, reason = _validate_state_persistence_directory(
            state_file_prefix=proposed_prefix
        )
        if not valid:
            raise ValueError(reason)
        persistence = ProviderStatePersistenceConfig(
            enabled=persistence.enabled,
            state_file_prefix=proposed_prefix,
            retention_count=persistence.retention_count,
            flush_mode=persistence.flush_mode,
            autosave_interval_seconds_since_change=(
                persistence.autosave_interval_seconds_since_change
            ),
        )
    if autosave_interval_seconds_since_change is not None:
        interval = int(autosave_interval_seconds_since_change)
        if interval <= 0:
            raise ValueError("autosave_interval_seconds_since_change must be positive")
        persistence = ProviderStatePersistenceConfig(
            enabled=persistence.enabled,
            state_file_prefix=persistence.state_file_prefix,
            retention_count=persistence.retention_count,
            flush_mode=persistence.flush_mode,
            autosave_interval_seconds_since_change=interval,
        )
    if retention_count is not None:
        keep = int(retention_count)
        if keep <= 0:
            raise ValueError("retention_count must be positive")
        persistence = ProviderStatePersistenceConfig(
            enabled=persistence.enabled,
            state_file_prefix=persistence.state_file_prefix,
            retention_count=keep,
            flush_mode=persistence.flush_mode,
            autosave_interval_seconds_since_change=(
                persistence.autosave_interval_seconds_since_change
            ),
        )
    config = ProviderConfig(
        delayed_comms_seconds=delayed,
        significant_comms_seconds=significant,
        webui_port=CONFIG.webui_port,
        minutes_keep_disconnected=keep_minutes,
        retry_after_seconds=CONFIG.retry_after_seconds,
        client_event_history_size=history_size,
        log_level=CONFIG.log_level,
        default_heartbeat_frequency=CONFIG.default_heartbeat_frequency,
        latest_docs_url=CONFIG.latest_docs_url,
        human_in_loop_approval=effective_human_in_loop_approval,
        allow_remote_config=CONFIG.allow_remote_config,
        allow_effective_config=CONFIG.allow_effective_config,
        allow_connection_settings=CONFIG.allow_connection_settings,
        allow_connection_settings_request=CONFIG.allow_connection_settings_request,
        allow_mcp=CONFIG.allow_mcp,
        opamp_use_authorization=CONFIG.opamp_use_authorization,
        ui_use_authorization=CONFIG.ui_use_authorization,
        metrics=CONFIG.metrics,
        tls=CONFIG.tls,
        state_persistence=persistence,
        observability=CONFIG.observability,
    )
    set_config(config)
    return config


def update_default_heartbeat_frequency(*, default_heartbeat_frequency: int) -> ProviderConfig:
    """Update the active default heartbeat frequency while preserving other settings.

    Parameters:
        default_heartbeat_frequency: New client heartbeat interval in seconds. Values below
            one are clamped to one second to keep the interval valid.

    Returns:
        Newly published provider configuration snapshot.
    """
    config = ProviderConfig(
        delayed_comms_seconds=CONFIG.delayed_comms_seconds,
        significant_comms_seconds=CONFIG.significant_comms_seconds,
        webui_port=CONFIG.webui_port,
        minutes_keep_disconnected=CONFIG.minutes_keep_disconnected,
        retry_after_seconds=CONFIG.retry_after_seconds,
        client_event_history_size=CONFIG.client_event_history_size,
        log_level=CONFIG.log_level,
        default_heartbeat_frequency=max(1, int(default_heartbeat_frequency)),
        latest_docs_url=CONFIG.latest_docs_url,
        human_in_loop_approval=CONFIG.human_in_loop_approval,
        allow_remote_config=CONFIG.allow_remote_config,
        allow_effective_config=CONFIG.allow_effective_config,
        allow_connection_settings=CONFIG.allow_connection_settings,
        allow_connection_settings_request=CONFIG.allow_connection_settings_request,
        allow_mcp=CONFIG.allow_mcp,
        opamp_use_authorization=CONFIG.opamp_use_authorization,
        ui_use_authorization=CONFIG.ui_use_authorization,
        metrics=CONFIG.metrics,
        tls=CONFIG.tls,
        state_persistence=CONFIG.state_persistence,
        observability=CONFIG.observability,
    )
    set_config(config)
    return config


def persist_provider_config(
    config: ProviderConfig | None = None,
    *,
    config_path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """Persist provider-owned settings to the shared OpAMP JSON configuration file.

    Unrelated top-level and component settings are preserved. A timestamped backup is created
    before the original file is replaced so an operator can recover the previous values.

    Parameters:
        config: Provider configuration to persist, or ``None`` to persist the active snapshot.
        config_path: Explicit target file, or ``None`` to use the effective configured path.

    Returns:
        Absolute path of the updated JSON configuration file.

    Raises:
        FileNotFoundError: If the target configuration file does not exist.
        json.JSONDecodeError: If the existing file contains invalid JSON.
        OSError: If backup creation or writing the updated file fails.
    """
    resolved_path = get_effective_config_path(config_path)
    raw = _load_json(resolved_path)
    provider_raw = raw.get(CFG_PROVIDER)
    if not isinstance(provider_raw, dict):
        provider_raw = {}
        raw[CFG_PROVIDER] = provider_raw

    effective = config or CONFIG
    provider_raw[CFG_DELAYED_COMMS_SECONDS] = int(effective.delayed_comms_seconds)
    provider_raw[CFG_SIGNIFICANT_COMMS_SECONDS] = int(
        effective.significant_comms_seconds
    )
    provider_raw[CFG_WEBUI_PORT] = int(effective.webui_port)
    provider_raw[CFG_MINUTES_KEEP_DISCONNECTED] = int(
        effective.minutes_keep_disconnected
    )
    provider_raw[CFG_RETRY_AFTER_SECONDS] = int(effective.retry_after_seconds)
    provider_raw[CFG_CLIENT_EVENT_HISTORY_SIZE] = int(effective.client_event_history_size)
    provider_raw[CFG_LOG_LEVEL] = str(effective.log_level)
    provider_raw[CFG_DEFAULT_HEARTBEAT_FREQUENCY] = int(
        effective.default_heartbeat_frequency
    )
    provider_raw[CFG_LATEST_DOCS_URL] = str(effective.latest_docs_url)
    provider_raw[CFG_HUMAN_IN_LOOP_APPROVAL] = bool(effective.human_in_loop_approval)
    provider_raw[CFG_ALLOW_REMOTE_CONFIG] = bool(effective.allow_remote_config)
    provider_raw[CFG_ALLOW_EFFECTIVE_CONFIG] = bool(effective.allow_effective_config)
    provider_raw[CFG_ALLOW_CONNECTION_SETTINGS] = bool(
        effective.allow_connection_settings
    )
    provider_raw[CFG_ALLOW_CONNECTION_SETTINGS_REQUEST] = bool(
        effective.allow_connection_settings_request
    )
    provider_raw[CFG_ALLOW_MCP] = bool(effective.allow_mcp)
    provider_raw[CFG_OPAMP_USE_AUTHORIZATION] = str(effective.opamp_use_authorization)
    provider_raw[CFG_UI_USE_AUTHORIZATION] = str(effective.ui_use_authorization)
    provider_raw[CFG_METRICS] = {
        CFG_METRICS_ENABLED: bool(effective.metrics.enabled),
        CFG_METRICS_GRAPH_HISTORY_MINUTES: int(
            effective.metrics.graph_history_minutes
        ),
    }
    provider_raw[CFG_STATE_PERSISTENCE] = {
        CFG_STATE_PERSISTENCE_ENABLED: bool(effective.state_persistence.enabled),
        CFG_STATE_FILE_PREFIX: str(effective.state_persistence.state_file_prefix),
        CFG_STATE_RETENTION_COUNT: int(effective.state_persistence.retention_count),
        CFG_STATE_FLUSH_MODE: str(effective.state_persistence.flush_mode),
        CFG_STATE_AUTOSAVE_INTERVAL: int(
            effective.state_persistence.autosave_interval_seconds_since_change
        ),
    }

    backup_path = _build_backup_path(resolved_path)
    logging.getLogger(__name__).info(
        "persist_provider_config backing up %s to %s before write",
        resolved_path,
        backup_path,
    )
    shutil.copy2(resolved_path, backup_path)

    resolved_path.write_text(
        f"{json.dumps(raw, indent=2)}\n",
        encoding=UTF8_ENCODING,
    )
    return resolved_path


def _build_backup_path(config_path: pathlib.Path) -> pathlib.Path:
    """Build a unique timestamped sibling path for a configuration backup.

    Parameters:
        config_path: Configuration file whose name and directory seed the backup path.

    Returns:
        Non-existing sibling path containing a high-resolution timestamp and, only when
        necessary, an incrementing collision suffix.
    """
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    backup_path = config_path.with_name(f"{config_path.name}.{timestamp}")
    suffix = 1
    while backup_path.exists():
        backup_path = config_path.with_name(f"{config_path.name}.{timestamp}.{suffix}")
        suffix += 1
    return backup_path


CONFIG = load_config()  # Module-level provider config singleton loaded at import time.
