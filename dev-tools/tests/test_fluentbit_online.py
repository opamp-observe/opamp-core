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

"""Tests for transient upstream Fluent Bit catalog loading."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from opamp_dev_tools import fluentbit_online


def test_load_online_catalog_uses_named_version_without_release_lookup(tmp_path: Path) -> None:
    """A named version should go directly to the configured documentation builder."""
    support_module = ModuleType("fake_support")
    calls: dict[str, object] = {}

    def fetch_url_text(url: str, *, timeout: int) -> str:
        """Fail if a named-version comparison unexpectedly requests the latest release."""
        raise AssertionError(f"Unexpected fetch: {url}, timeout={timeout}")

    def build_catalog_from_docs(version: str, **options: object) -> dict[str, object]:
        """Capture the online scraper arguments and return a minimal catalog."""
        calls["version"] = version
        calls["options"] = options
        return {"plugins": {}}

    support_module.fetch_url_text = fetch_url_text  # type: ignore[attr-defined]
    support_module.build_catalog_from_docs = build_catalog_from_docs  # type: ignore[attr-defined]

    version, catalog = fluentbit_online.load_online_catalog(
        tmp_path,
        version="v5.1.3",
        source="github",
        github_ref="v5.1.3",
        timeout=17,
        support_loader=lambda _: support_module,
    )

    assert version == "5.1.3"
    assert catalog == {"plugins": {}}
    assert calls["version"] == "5.1.3"
    options = calls["options"]
    assert isinstance(options, dict)
    assert options["source"] == "github"
    assert options["timeout"] == 17
    assert options["github_ref"] == "v5.1.3"
    assert options["text_fetcher"] is fetch_url_text


def test_load_online_catalog_resolves_current_release(tmp_path: Path) -> None:
    """An omitted version should use the latest stable GitHub release tag."""
    support_module = ModuleType("fake_support")
    requested_urls: list[str] = []

    def fetch_url_text(url: str, *, timeout: int) -> str:
        """Return a deterministic latest-release response for the loader."""
        requested_urls.append(f"{url}:{timeout}")
        return '{"tag_name": "v6.2.1"}'

    def build_catalog_from_docs(version: str, **_options: object) -> dict[str, object]:
        """Return a catalog labelled by the resolved current version."""
        return {"resolved": version}

    support_module.fetch_url_text = fetch_url_text  # type: ignore[attr-defined]
    support_module.build_catalog_from_docs = build_catalog_from_docs  # type: ignore[attr-defined]

    version, catalog = fluentbit_online.load_online_catalog(
        tmp_path,
        support_loader=lambda _: support_module,
    )

    assert version == "6.2.1"
    assert catalog == {"resolved": "6.2.1"}
    assert requested_urls == [f"{fluentbit_online.FLUENTBIT_LATEST_RELEASE_URL}:30"]


@pytest.mark.parametrize(
    ("release_text", "message"),
    [
        ("not-json", "not valid JSON"),
        ("[]", "must be a JSON object"),
        ('{"tag_name": "next"}', "did not provide a semantic"),
        ("{}", "did not provide a semantic"),
    ],
)
def test_current_release_resolution_rejects_invalid_payloads(
    release_text: str,
    message: str,
) -> None:
    """Malformed GitHub release responses should fail with an actionable message."""

    def fetch_release(_url: str, *, timeout: int) -> str:
        """Return the parameterized response without network access."""
        assert timeout == 9
        return release_text

    with pytest.raises(ValueError, match=message):
        fluentbit_online.resolve_current_online_version(
            timeout=9,
            text_fetcher=fetch_release,
        )


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"timeout": 0}, "greater than zero"),
        ({"source": "mirror"}, "Unsupported Fluent Bit documentation source"),
        ({"version": "latest"}, "Unsupported Fluent Bit version"),
    ],
)
def test_load_online_catalog_rejects_invalid_options(
    tmp_path: Path,
    options: dict[str, object],
    message: str,
) -> None:
    """Invalid network and version choices should fail before scraping."""
    support_module = ModuleType("fake_support")
    support_module.fetch_url_text = lambda *_args, **_kwargs: "{}"  # type: ignore[attr-defined]
    support_module.build_catalog_from_docs = lambda *_args, **_kwargs: {}  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match=message):
        fluentbit_online.load_online_catalog(
            tmp_path,
            support_loader=lambda _: support_module,
            **options,
        )


def test_load_online_catalog_rejects_invalid_support_and_result(tmp_path: Path) -> None:
    """Missing scraper callables and non-object catalogs should not be accepted."""
    missing_fetcher = ModuleType("missing_fetcher")
    with pytest.raises(ImportError, match="fetch_url_text"):
        fluentbit_online.load_online_catalog(
            tmp_path,
            version="5.1.3",
            support_loader=lambda _: missing_fetcher,
        )

    invalid_result = ModuleType("invalid_result")
    invalid_result.fetch_url_text = lambda *_args, **_kwargs: "{}"  # type: ignore[attr-defined]
    invalid_result.build_catalog_from_docs = lambda *_args, **_kwargs: []  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="non-object catalog"):
        fluentbit_online.load_online_catalog(
            tmp_path,
            version="5.1.3",
            support_loader=lambda _: invalid_result,
        )


def test_repository_support_module_loader_executes_exact_source(tmp_path: Path) -> None:
    """The loader should execute the Config Service helper without changing sys.path."""
    module_path = tmp_path / fluentbit_online.CONFIG_SERVICE_DOCS_SUPPORT_PATH
    module_path.parent.mkdir(parents=True)
    module_path.write_text(
        "def fetch_url_text(*args, **kwargs):\n    return 'text'\n\n"
        "def build_catalog_from_docs(*args, **kwargs):\n    return {'plugins': {}}\n",
        encoding="utf-8",
    )
    previous_module = ModuleType("previous_support")
    sys.modules[fluentbit_online.SUPPORT_MODULE_NAME] = previous_module

    loaded_module = fluentbit_online._load_docs_support_module(  # pylint: disable=protected-access
        tmp_path
    )

    assert loaded_module.fetch_url_text() == "text"
    assert sys.modules[fluentbit_online.SUPPORT_MODULE_NAME] is previous_module
    sys.modules.pop(fluentbit_online.SUPPORT_MODULE_NAME)

    reloaded_module = fluentbit_online._load_docs_support_module(  # pylint: disable=protected-access
        tmp_path
    )

    assert reloaded_module.fetch_url_text() == "text"
    assert fluentbit_online.SUPPORT_MODULE_NAME not in sys.modules


def test_repository_support_module_loader_rejects_missing_or_unloadable_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing or unloadable Config Service helper should fail clearly."""
    with pytest.raises(FileNotFoundError, match="scraper not found"):
        fluentbit_online._load_docs_support_module(  # pylint: disable=protected-access
            tmp_path
        )

    module_path = tmp_path / fluentbit_online.CONFIG_SERVICE_DOCS_SUPPORT_PATH
    module_path.parent.mkdir(parents=True)
    module_path.write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.setattr(fluentbit_online.importlib.util, "spec_from_file_location", lambda *_: None)
    with pytest.raises(ImportError, match="Unable to load"):
        fluentbit_online._load_docs_support_module(  # pylint: disable=protected-access
            tmp_path
        )
