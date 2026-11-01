# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Config-service JSON schema and definition validation helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .runtime import CommandRuntime


def validate_config_service_schemas(runtime: CommandRuntime) -> bool:
    """Validate config-service JSON artifacts from the master source tree."""
    config_service_root = runtime.repo_root / "config-service"
    src_root = config_service_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from config_service.json_artifacts import load_json_artifact, load_json_schema_artifact

    any_issues = False
    validation_targets = (
        (src_root / "config_service" / "json-definitions", load_json_artifact, False),
        (src_root / "config_service" / "json-schemas", load_json_schema_artifact, True),
    )
    for root_dir, loader, is_schema in validation_targets:
        if not root_dir.exists():
            continue
        for json_path in sorted(root_dir.rglob("*.json")):
            try:
                payload = _assert_json_loadable(json_path)
                should_resolve = json_path.parent == root_dir
                if should_resolve:
                    payload = loader(json_path)
            except Exception as exc:  # pylint: disable=broad-except
                runtime.record_issue(
                    f"validation failed: {exc}",
                    category="schema-validation" if is_schema else "definition-validation",
                    path=json_path,
                    details={"exception": repr(exc)},
                )
                any_issues = True
    if not any_issues:
        runtime.info("Schema validation completed without issues.")
    return any_issues


def _assert_json_loadable(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
