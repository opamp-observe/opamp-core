# Copyright 2026 mp3monster.org
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

"""Load a transient Fluent Bit catalog from upstream documentation."""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

CONFIG_SERVICE_DOCS_SUPPORT_PATH = Path(
    "config-service/src/config_service/fluentbit_docs_support.py"
)
DEFAULT_DOCUMENTATION_SOURCE = "auto"
DEFAULT_ONLINE_TIMEOUT_SECONDS = 30
DOCUMENTATION_SOURCES = ("auto", "github", "website")
FLUENTBIT_LATEST_RELEASE_URL = "https://api.github.com/repos/fluent/fluent-bit/releases/latest"
KEY_TAG_NAME = "tag_name"
SUPPORT_MODULE_NAME = "_opamp_dev_tools_fluentbit_docs_support"
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

DocsBuilder = Callable[..., dict[str, Any]]
SupportLoader = Callable[[Path], ModuleType]
TextFetcher = Callable[..., str]


def load_online_catalog(  # pylint: disable=too-many-arguments
    repo_root: Path,
    *,
    version: str = "",
    source: str = DEFAULT_DOCUMENTATION_SOURCE,
    github_ref: str = "",
    timeout: int = DEFAULT_ONLINE_TIMEOUT_SECONDS,
    support_loader: SupportLoader | None = None,
) -> tuple[str, dict[str, Any]]:
    """Build an upstream catalog in memory without changing repository data.

    Parameters
    ----------
    repo_root:
        Repository containing the Config Service documentation scraper.
    version:
        Optional Fluent Bit version. The current GitHub release is used when empty.
    source:
        Documentation source selection: auto, GitHub, or published website.
    github_ref:
        Optional Git ref override used by the GitHub documentation scraper.
    timeout:
        Per-request network timeout in seconds.
    support_loader:
        Optional loader used by tests to provide the Config Service scraper module.

    """
    if timeout <= 0:
        raise ValueError("Online timeout must be greater than zero seconds")
    if source not in DOCUMENTATION_SOURCES:
        raise ValueError(f"Unsupported Fluent Bit documentation source '{source}'")

    active_loader = support_loader or _load_docs_support_module
    support_module = active_loader(repo_root)
    text_fetcher = _required_callable(support_module, "fetch_url_text")
    docs_builder = _required_callable(support_module, "build_catalog_from_docs")
    resolved_version = _normalize_version(version)
    if not resolved_version:
        resolved_version = resolve_current_online_version(
            timeout=timeout,
            text_fetcher=text_fetcher,
        )
    catalog = docs_builder(  # pylint: disable=not-callable
        resolved_version,
        source=source,
        timeout=timeout,
        github_ref=github_ref or None,
        logger=LOGGER,
        text_fetcher=text_fetcher,
    )
    if not isinstance(catalog, dict):
        raise ValueError("Fluent Bit documentation scraper returned a non-object catalog")
    return resolved_version, catalog


def resolve_current_online_version(
    *,
    timeout: int,
    text_fetcher: TextFetcher,
) -> str:
    """Resolve the current stable Fluent Bit version from its latest GitHub release.

    Parameters
    ----------
    timeout:
        Per-request network timeout in seconds.
    text_fetcher:
        HTTP text loader supplied by the Config Service scraper.

    """
    release_text = text_fetcher(FLUENTBIT_LATEST_RELEASE_URL, timeout=timeout)
    try:
        release_payload = json.loads(release_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Fluent Bit latest-release response is not valid JSON") from exc
    if not isinstance(release_payload, Mapping):
        raise ValueError("Fluent Bit latest-release response must be a JSON object")
    try:
        resolved_version = _normalize_version(str(release_payload.get(KEY_TAG_NAME, "")))
    except ValueError as exc:
        raise ValueError("Fluent Bit latest release did not provide a semantic tag_name") from exc
    if not resolved_version:
        raise ValueError("Fluent Bit latest release did not provide a semantic tag_name")
    return resolved_version


def _load_docs_support_module(repo_root: Path) -> ModuleType:
    """Load the Config Service scraper module directly from the repository.

    Parameters
    ----------
    repo_root:
        Repository expected to contain the Config Service source tree.

    """
    module_path = (repo_root / CONFIG_SERVICE_DOCS_SUPPORT_PATH).resolve()
    if not module_path.is_file():
        raise FileNotFoundError(f"Fluent Bit documentation scraper not found: {module_path}")
    module_spec = importlib.util.spec_from_file_location(SUPPORT_MODULE_NAME, module_path)
    if module_spec is None or module_spec.loader is None:
        raise ImportError(f"Unable to load Fluent Bit documentation scraper: {module_path}")
    support_module = importlib.util.module_from_spec(module_spec)
    previous_module = sys.modules.get(SUPPORT_MODULE_NAME)
    sys.modules[SUPPORT_MODULE_NAME] = support_module
    try:
        module_spec.loader.exec_module(support_module)
    finally:
        if previous_module is None:
            sys.modules.pop(SUPPORT_MODULE_NAME, None)
        else:
            sys.modules[SUPPORT_MODULE_NAME] = previous_module
    return support_module


def _required_callable(module: ModuleType, attribute_name: str) -> Callable[..., Any]:
    """Return a required callable exported by the scraper support module.

    Parameters
    ----------
    module:
        Dynamically loaded Config Service support module.
    attribute_name:
        Public function name required by the online comparison.

    """
    value = getattr(module, attribute_name, None)
    if not callable(value):
        raise ImportError(f"Fluent Bit documentation scraper has no callable '{attribute_name}'")
    return value


def _normalize_version(version: str) -> str:
    """Normalize and validate an optional dotted Fluent Bit version.

    Parameters
    ----------
    version:
        User-supplied version or GitHub tag, optionally prefixed with ``v``.

    """
    normalized_version = version.strip().removeprefix("v")
    if normalized_version and re.fullmatch(r"\d+(?:\.\d+)*", normalized_version) is None:
        raise ValueError(f"Unsupported Fluent Bit version '{version}'")
    return normalized_version
