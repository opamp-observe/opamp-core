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

"""Contract tests for the source-mounted client-config-generator deployment."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "test-containers"
    / "client-config-generator-service-deployment"
    / "scripts"
    / "verify_deployment.py"
)
VERIFIER_MODULE_NAME = "client_config_generator_deployment_verifier"


def _load_verifier_module() -> ModuleType:
    """Load the deployment verifier without executing its command-line entry point."""
    module_spec = importlib.util.spec_from_file_location(VERIFIER_MODULE_NAME, VERIFIER_PATH)
    assert module_spec is not None
    assert module_spec.loader is not None
    verifier_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(verifier_module)
    return verifier_module


def test_verifier_adds_every_src_layout_package_root() -> None:
    """Expose shared, provider, and generator source packages inside the clean container."""
    verifier_module = _load_verifier_module()
    original_import_paths = list(sys.path)
    expected_source_paths = {
        str((REPOSITORY_ROOT / "shared" / "src").resolve()),
        str((REPOSITORY_ROOT / "provider" / "src").resolve()),
        str((REPOSITORY_ROOT / "client-config-generator-service" / "src").resolve()),
    }

    try:
        verifier_module._configure_import_paths(  # pylint: disable=protected-access
            REPOSITORY_ROOT
        )
        assert expected_source_paths.issubset(set(sys.path))
    finally:
        sys.path[:] = original_import_paths
