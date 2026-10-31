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

"""Provider runtime state snapshot persistence helpers."""

from __future__ import annotations

import json
import logging
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import Any

from opamp_provider.config import ProviderStatePersistenceConfig
from opamp_provider.metrics import PROVIDER_METRICS
from opamp_provider.state import ClientStore
from shared.opamp_config import UTF8_ENCODING

SCHEMA_VERSION = 1  # Version marker for persisted state snapshot payloads.
RESTORE_AUTO = "__AUTO__"  # CLI restore sentinel meaning "load latest snapshot".
TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"  # UTC timestamp suffix format for snapshot file names.


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def _checkpoint_timestamp(saved_at_utc: object) -> float:
    """Return Unix seconds for a saved-at timestamp when it can be parsed."""
    try:
        if isinstance(saved_at_utc, datetime):
            value = saved_at_utc
        else:
            text = str(saved_at_utc or "").strip()
            if not text:
                return 0.0
            value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return 0.0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return float(value.timestamp())


def _snapshot_name(prefix_path: pathlib.Path, *, now: datetime | None = None) -> str:
    """Return snapshot filename using UTC timestamp suffix."""
    ts = (now or _utc_now()).strftime(TIMESTAMP_FORMAT)
    return f"{prefix_path.name}.{ts}.json"


def _snapshot_directory(prefix_path: pathlib.Path) -> pathlib.Path:
    """Resolve snapshot directory from configured prefix path."""
    directory = prefix_path.parent
    if str(directory).strip() in {"", "."}:
        return pathlib.Path.cwd()
    return directory


def _snapshot_path(
    prefix: str,
    *,
    now: datetime | None = None,
) -> pathlib.Path:
    """Return a timestamped snapshot path for the provided prefix."""
    prefix_path = pathlib.Path(prefix)
    directory = _snapshot_directory(prefix_path)
    return directory / _snapshot_name(prefix_path, now=now)


def _snapshot_regex(prefix_path: pathlib.Path) -> re.Pattern[str]:
    """Build filename matcher for snapshots derived from prefix."""
    escaped = re.escape(prefix_path.name)
    return re.compile(rf"^{escaped}\.(\d{{8}}T\d{{6}}Z)\.json$")


def list_snapshot_files(prefix: str) -> list[pathlib.Path]:
    """List snapshot files for configured prefix sorted latest-first."""
    prefix_path = pathlib.Path(prefix)
    directory = _snapshot_directory(prefix_path)
    if not directory.exists():
        return []
    pattern = _snapshot_regex(prefix_path)
    matches: list[tuple[str, pathlib.Path]] = []
    for candidate in directory.glob(f"{prefix_path.name}.*.json"):
        match = pattern.match(candidate.name)
        if not match:
            continue
        matches.append((match.group(1), candidate))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [path for _suffix, path in matches]


def prune_snapshot_files(
    *,
    state_file_prefix: str,
    retention_count: int,
    logger: logging.Logger | None = None,
) -> int:
    """Prune stale snapshot files to configured retention and return removed count."""
    log = logger or logging.getLogger(__name__)
    snapshots = list_snapshot_files(state_file_prefix)
    keep = max(1, int(retention_count))
    removed = 0
    started_at = time.perf_counter()
    for stale in snapshots[keep:]:
        try:
            stale.unlink(missing_ok=True)
            removed += 1
        except Exception as exc:
            log.warning("failed pruning stale snapshot path=%s", stale, exc_info=exc)
            PROVIDER_METRICS.increment_counter(
                "opamp_provider_persistence_failures_total",
                labels={"backend": "json_file", "operation": "snapshot_prune"},
            )
    if removed:
        PROVIDER_METRICS.increment_counter(
            "opamp_provider_persistence_mutations_total",
            labels={"backend": "json_file", "op": "prune"},
            amount=float(removed),
        )
        PROVIDER_METRICS.observe_histogram(
            "opamp_provider_persistence_write_seconds",
            time.perf_counter() - started_at,
            labels={"backend": "json_file", "operation": "snapshot_prune"},
        )
    return removed


def resolve_restore_snapshot_path(
    *,
    state_file_prefix: str,
    restore_option: str | None,
) -> pathlib.Path:
    """Resolve restore snapshot path from explicit or auto restore option."""
    if restore_option and restore_option != RESTORE_AUTO:
        return pathlib.Path(restore_option)
    snapshots = list_snapshot_files(state_file_prefix)
    if not snapshots:
        raise FileNotFoundError(
            f"no snapshots found for state_file_prefix={state_file_prefix}"
        )
    return snapshots[0]


def save_state_snapshot(
    *,
    store: ClientStore,
    persistence: ProviderStatePersistenceConfig,
    reason: str,
    logger: logging.Logger | None = None,
    now: datetime | None = None,
) -> pathlib.Path | None:
    """Persist one timestamped provider state snapshot and prune old files."""
    log = logger or logging.getLogger(__name__)
    if persistence.enabled is not True:
        return None
    path = _snapshot_path(persistence.state_file_prefix, now=now)
    path.parent.mkdir(parents=True, exist_ok=True)
    started_at = time.perf_counter()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "saved_at_utc": (now or _utc_now()).replace(microsecond=0).isoformat(),
        "provider_state": store.export_persisted_state(),
    }
    try:
        path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding=UTF8_ENCODING)
        PROVIDER_METRICS.increment_counter(
            "opamp_provider_persistence_mutations_total",
            labels={"backend": "json_file", "op": "save"},
        )
        PROVIDER_METRICS.observe_histogram(
            "opamp_provider_persistence_write_seconds",
            time.perf_counter() - started_at,
            labels={"backend": "json_file", "operation": "snapshot_save"},
        )
        PROVIDER_METRICS.set_runtime_gauge(
            "opamp_provider_last_checkpoint_timestamp_seconds",
            _checkpoint_timestamp(payload["saved_at_utc"]),
        )
        prune_snapshot_files(
            state_file_prefix=persistence.state_file_prefix,
            retention_count=persistence.retention_count,
            logger=log,
        )
        PROVIDER_METRICS.capture_gauge_series(store)
        log.info("state snapshot saved reason=%s path=%s", reason, path)
        return path
    except Exception:
        PROVIDER_METRICS.increment_counter(
            "opamp_provider_persistence_failures_total",
            labels={"backend": "json_file", "operation": "snapshot_save"},
        )
        raise


def restore_state_snapshot(
    *,
    store: ClientStore,
    snapshot_path: pathlib.Path,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Restore provider state from one snapshot path."""
    log = logger or logging.getLogger(__name__)
    try:
        payload = json.loads(snapshot_path.read_text(encoding=UTF8_ENCODING))
        if not isinstance(payload, dict):
            raise ValueError("snapshot payload must be a JSON object")
        schema_version = payload.get("schema_version")
        if schema_version != SCHEMA_VERSION:
            log.warning(
                "state snapshot schema mismatch snapshot=%s expected=%s actual=%s; attempting compatible restore",
                snapshot_path,
                SCHEMA_VERSION,
                schema_version,
            )
        provider_state = payload.get("provider_state")
        summary = store.import_persisted_state(provider_state)
        result: dict[str, Any] = {
            "snapshot_path": str(snapshot_path),
            "schema_version": schema_version,
            "saved_at_utc": payload.get("saved_at_utc"),
        }
        result.update(summary)
        PROVIDER_METRICS.increment_counter(
            "opamp_provider_restore_operations_total",
            labels={"backend": "json_file", "result": "success"},
        )
        checkpoint_seconds = _checkpoint_timestamp(payload.get("saved_at_utc"))
        if checkpoint_seconds > 0:
            PROVIDER_METRICS.set_runtime_gauge(
                "opamp_provider_last_checkpoint_timestamp_seconds",
                checkpoint_seconds,
            )
        PROVIDER_METRICS.capture_gauge_series(store)
        log.info(
            (
                "state snapshot restored path=%s clients=%s pending_approvals=%s "
                "blocked_agents=%s pending_instance_uid_replacements=%s full_refresh_queued=%s"
            ),
            snapshot_path,
            summary.get("clients", 0),
            summary.get("pending_approvals", 0),
            summary.get("blocked_agents", 0),
            summary.get("pending_instance_uid_replacements", 0),
            summary.get("full_refresh_queued", 0),
        )
        return result
    except Exception:
        PROVIDER_METRICS.increment_counter(
            "opamp_provider_restore_operations_total",
            labels={"backend": "json_file", "result": "failure"},
        )
        PROVIDER_METRICS.increment_counter(
            "opamp_provider_persistence_failures_total",
            labels={"backend": "json_file", "operation": "restore"},
        )
        raise
