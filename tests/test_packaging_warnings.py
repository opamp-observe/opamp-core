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

from __future__ import annotations

from pathlib import Path

import pytest

from shared import packaging_warnings
from shared.packaging_warnings import build_cli_missing_warning


def test_build_cli_missing_warning_returns_none_when_workspace_cli_exists() -> None:
    warning = build_cli_missing_warning(
        component_label="provider wheel build",
        repo_root=Path(__file__).resolve().parents[1],
    )

    assert warning is None


def test_build_cli_missing_warning_reports_missing_cli(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(packaging_warnings, "_detect_cli_distribution", lambda: None)
    warning = build_cli_missing_warning(
        component_label="provider wheel build",
        repo_root=tmp_path,
    )

    assert warning is not None
    assert "provider wheel build" in warning
    assert "did not detect the OpAMP CLI" in warning
