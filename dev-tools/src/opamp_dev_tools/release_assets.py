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

"""Composite wheel, SBOM, and release-asset build helpers for the developer CLI."""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .components import build_component_wheel, select_components
from .provider_ui import compact_provider_ui_assets
from .security import run_repo_security_checks
from .version_metadata import main as refresh_version_metadata

DEFAULT_REPO = "mp3monster/fluent-opamp"
DEFAULT_MANUAL_PATH = "dist/manual/opamp_manual.pdf"
DEFAULT_RELEASE_COMPONENT_KEYS = (
    "provider",
    "consumer",
    "catalog-service",
    "client-config-generator-service",
    "cli",
    "consumer-sim",
)
LEGACY_DEFAULT_PROVIDER_SBOM_PATH = (
    "dist/sbom/opamp_provider_deployable_artifacts.cyclonedx.json"
)
LEGACY_DEFAULT_CONSUMER_SBOM_PATH = (
    "dist/sbom/opamp_consumer_deployable_artifacts.cyclonedx.json"
)
DEFAULT_RELEASE_NOTES = "Automated wheel upload from dev-tools build release-assets"
COMPONENT_KEY_ALIASES = {
    "catalog": "catalog-service",
}


@dataclass(frozen=True)
class ReleaseComponentTarget:
    """One independently deployable wheel-and-SBOM release target."""

    key: str
    source_dir: str
    dist_dirname: str
    root_component_name: str
    default_sbom_relpath: str
    display_name: str


RELEASE_COMPONENT_TARGETS: dict[str, ReleaseComponentTarget] = {
    "provider": ReleaseComponentTarget(
        key="provider",
        source_dir="provider",
        dist_dirname="provider",
        root_component_name="fluent-opamp-provider-deployable-artifact",
        default_sbom_relpath="dist/sbom/opamp_provider_deployable_artifacts.cyclonedx.json",
        display_name="Provider",
    ),
    "consumer": ReleaseComponentTarget(
        key="consumer",
        source_dir="consumer",
        dist_dirname="consumer",
        root_component_name="fluent-opamp-consumer-deployable-artifact",
        default_sbom_relpath="dist/sbom/opamp_consumer_deployable_artifacts.cyclonedx.json",
        display_name="Consumer",
    ),
    "catalog-service": ReleaseComponentTarget(
        key="catalog-service",
        source_dir="catalog-service",
        dist_dirname="catalog",
        root_component_name="fluent-opamp-catalog-service-deployable-artifact",
        default_sbom_relpath="dist/sbom/opamp_catalog_service_deployable_artifacts.cyclonedx.json",
        display_name="Catalog service",
    ),
    "client-config-generator-service": ReleaseComponentTarget(
        key="client-config-generator-service",
        source_dir="client-config-generator-service",
        dist_dirname="client-config-generator-service",
        root_component_name="fluent-opamp-client-config-generator-service-deployable-artifact",
        default_sbom_relpath=(
            "dist/sbom/opamp_client_config_generator_service_deployable_artifacts.cyclonedx.json"
        ),
        display_name="Client config generator service",
    ),
    "cli": ReleaseComponentTarget(
        key="cli",
        source_dir="cli",
        dist_dirname="cli",
        root_component_name="fluent-opamp-cli-deployable-artifact",
        default_sbom_relpath="dist/sbom/opamp_cli_deployable_artifacts.cyclonedx.json",
        display_name="CLI",
    ),
    "consumer-sim": ReleaseComponentTarget(
        key="consumer-sim",
        source_dir="consumer-sim",
        dist_dirname="consumer-sim",
        root_component_name="fluent-opamp-consumer-sim-deployable-artifact",
        default_sbom_relpath="dist/sbom/opamp_consumer_sim_deployable_artifacts.cyclonedx.json",
        display_name="Consumer simulator",
    ),
}


def add_release_assets_arguments(parser: Any) -> None:
    """Attach release-asset build arguments to one argparse parser."""
    component_help = ", ".join(DEFAULT_RELEASE_COMPONENT_KEYS)
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repository in owner/name form (default: {DEFAULT_REPO})",
    )
    parser.add_argument(
        "--components",
        default=",".join(DEFAULT_RELEASE_COMPONENT_KEYS),
        help=(
            "Comma-separated component keys to build "
            f"(default: {component_help}; alias `catalog` is also accepted)"
        ),
    )
    parser.add_argument(
        "--dist-root",
        default="dist",
        help="Artefact root directory (default: dist)",
    )
    parser.add_argument(
        "--provider-sbom-path",
        default=LEGACY_DEFAULT_PROVIDER_SBOM_PATH,
        help=(
            "Provider SBOM output path "
            f"(default: {LEGACY_DEFAULT_PROVIDER_SBOM_PATH})"
        ),
    )
    parser.add_argument(
        "--consumer-sbom-path",
        default=LEGACY_DEFAULT_CONSUMER_SBOM_PATH,
        help=(
            "Consumer SBOM output path "
            f"(default: {LEGACY_DEFAULT_CONSUMER_SBOM_PATH})"
        ),
    )
    parser.add_argument(
        "--component-sbom-path",
        action="append",
        default=[],
        help="Override one component SBOM path using KEY=PATH",
    )
    parser.add_argument(
        "--manual-path",
        default=DEFAULT_MANUAL_PATH,
        help=f"PDF manual output path (default: {DEFAULT_MANUAL_PATH})",
    )
    parser.add_argument(
        "--skip-manual",
        action="store_true",
        help="Skip PDF manual refresh step",
    )
    parser.add_argument(
        "--skip-ui-compaction",
        action="store_true",
        help="Skip provider web UI JavaScript compaction step",
    )
    parser.add_argument(
        "--skip-security-checks",
        action="store_true",
        help="Skip consolidated security checks workflow step",
    )
    parser.add_argument(
        "--no-isolation",
        action="store_true",
        help="Pass --no-isolation to python -m build for local/offline builds",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish built wheels to a GitHub release",
    )
    parser.add_argument(
        "--tag",
        help="Release tag used when publishing (required with --publish)",
    )
    parser.add_argument(
        "--release-name",
        help="Release name/title (defaults to tag)",
    )
    parser.add_argument(
        "--release-notes",
        default="",
        help="Release notes text for new release creation",
    )
    parser.add_argument(
        "--release-notes-file",
        help="Path to markdown/text file used as release notes body",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Create the release as draft when publishing",
    )
    parser.add_argument(
        "--prerelease",
        action="store_true",
        help="Mark the release as prerelease when publishing",
    )
    parser.add_argument(
        "--github-token",
        default="",
        help="GitHub token (default: env GITHUB_TOKEN or GH_TOKEN)",
    )


def parse_release_component_keys(raw_components: str) -> list[str]:
    """Parse and validate selected component keys."""
    raw_keys = [item.strip() for item in str(raw_components or "").split(",") if item.strip()]
    if not raw_keys:
        raise ValueError("at least one component must be selected")
    normalized_keys: list[str] = []
    for raw_key in raw_keys:
        normalized_keys.append(COMPONENT_KEY_ALIASES.get(raw_key, raw_key))
    invalid = [item for item in normalized_keys if item not in RELEASE_COMPONENT_TARGETS]
    if invalid:
        valid_keys = ", ".join(sorted(RELEASE_COMPONENT_TARGETS))
        raise ValueError(
            f"unknown component(s): {', '.join(invalid)}; valid values: {valid_keys}"
        )
    deduped: list[str] = []
    seen: set[str] = set()
    for key in normalized_keys:
        if key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped


def resolve_release_sbom_paths(
    *,
    repo_root: Path,
    component_keys: list[str],
    provider_sbom_path: str,
    consumer_sbom_path: str,
    component_sbom_path_overrides: list[str],
) -> dict[str, Path]:
    """Resolve SBOM output paths for all selected components."""
    sbom_paths = {
        key: _resolve_repo_path(
            repo_root,
            RELEASE_COMPONENT_TARGETS[key].default_sbom_relpath,
        )
        for key in component_keys
    }
    if "provider" in sbom_paths:
        sbom_paths["provider"] = _resolve_repo_path(repo_root, provider_sbom_path)
    if "consumer" in sbom_paths:
        sbom_paths["consumer"] = _resolve_repo_path(repo_root, consumer_sbom_path)
    for override in component_sbom_path_overrides:
        raw_key, separator, raw_path = override.partition("=")
        if separator != "=" or not raw_key.strip() or not raw_path.strip():
            raise ValueError(
                "--component-sbom-path must use KEY=PATH, for example "
                "catalog-service=dist/sbom/catalog.cyclonedx.json"
            )
        normalized_key = COMPONENT_KEY_ALIASES.get(raw_key.strip(), raw_key.strip())
        if normalized_key not in RELEASE_COMPONENT_TARGETS:
            raise ValueError(f"unknown component in --component-sbom-path: {normalized_key}")
        sbom_paths[normalized_key] = _resolve_repo_path(repo_root, raw_path.strip())
    return sbom_paths


def build_release_assets(
    runtime: Any,
    *,
    repo: str,
    component_keys: list[str],
    dist_root: str,
    resolved_sbom_paths: dict[str, Path],
    manual_path: str,
    skip_manual: bool,
    skip_ui_compaction: bool,
    skip_security_checks: bool,
    python_exe: str,
    no_isolation: bool,
    publish: bool,
    tag: str | None,
    release_name: str | None,
    release_notes: str,
    release_notes_file: str | None,
    draft: bool,
    prerelease: bool,
    github_token: str,
) -> bool:
    """Build release-ready wheels and SBOMs, then optionally publish them."""
    _validate_release_asset_arguments(
        publish=publish,
        tag=tag,
        release_notes=release_notes,
        release_notes_file=release_notes_file,
    )
    refresh_version_metadata(["--repo-root", str(runtime.repo_root), "--quiet"])
    manual_pdf = _prepare_release_supporting_assets(
        runtime,
        python_exe=python_exe,
        manual_path=manual_path,
        skip_manual=skip_manual,
        skip_ui_compaction=skip_ui_compaction,
        skip_security_checks=skip_security_checks,
    )
    built_wheels, built_sboms = _build_release_component_outputs(
        runtime,
        repo=repo,
        component_keys=component_keys,
        dist_root=dist_root,
        resolved_sbom_paths=resolved_sbom_paths,
        python_exe=python_exe,
        no_isolation=no_isolation,
    )
    _log_release_build_results(
        runtime,
        component_keys=component_keys,
        built_wheels=built_wheels,
        built_sboms=built_sboms,
        manual_pdf=manual_pdf,
    )
    if not publish:
        runtime.info("Publish skipped (use --publish to upload to GitHub release assets).")
        return False
    _publish_release_build_outputs(
        runtime,
        repo=repo,
        tag=str(tag),
        release_name=release_name,
        release_notes=release_notes,
        release_notes_file=release_notes_file,
        draft=draft,
        prerelease=prerelease,
        github_token=github_token,
        component_keys=component_keys,
        built_wheels=built_wheels,
        built_sboms=built_sboms,
        manual_pdf=manual_pdf,
    )
    return False


def _validate_release_asset_arguments(
    *,
    publish: bool,
    tag: str | None,
    release_notes: str,
    release_notes_file: str | None,
) -> None:
    """Validate mutually dependent release-assets command arguments."""
    if publish and not str(tag or "").strip():
        raise RuntimeError("--tag is required when --publish is provided")
    if release_notes and release_notes_file:
        raise RuntimeError("use either --release-notes or --release-notes-file, not both")


def _prepare_release_supporting_assets(
    runtime: Any,
    *,
    python_exe: str,
    manual_path: str,
    skip_manual: bool,
    skip_ui_compaction: bool,
    skip_security_checks: bool,
) -> Path | None:
    """Refresh supporting artefacts that are not component-specific."""
    if not skip_security_checks:
        run_repo_security_checks(runtime, python_exe=python_exe)
    elif not skip_ui_compaction:
        _refresh_provider_ui_compact_assets(runtime, python_exe=python_exe)
    return _build_manual_if_requested(
        runtime,
        python_exe=python_exe,
        manual_path=manual_path,
        skip_manual=skip_manual,
    )


def _build_manual_if_requested(
    runtime: Any,
    *,
    python_exe: str,
    manual_path: str,
    skip_manual: bool,
) -> Path | None:
    """Build the PDF manual when the release workflow requires it."""
    if skip_manual:
        return None
    manual_output_path = _resolve_repo_path(runtime.repo_root, manual_path)
    _build_pdf(runtime, python_exe=python_exe, output=str(manual_output_path))
    if not manual_output_path.exists():
        raise RuntimeError(
            f"manual build did not produce expected file: {manual_output_path}"
        )
    return manual_output_path


def _build_release_component_outputs(
    runtime: Any,
    *,
    repo: str,
    component_keys: list[str],
    dist_root: str,
    resolved_sbom_paths: dict[str, Path],
    python_exe: str,
    no_isolation: bool,
) -> tuple[dict[str, Path], dict[str, Path]]:
    """Build wheels and SBOMs for each selected release component."""
    if str(runtime.repo_root) not in sys.path:
        sys.path.insert(0, str(runtime.repo_root))
    from opamp_dev_tools.sbom import (
        validate_wheel_artifact_sbom,
        write_wheel_artifact_sbom,
    )

    dist_root_path = _resolve_repo_path(runtime.repo_root, dist_root)
    built_wheels: dict[str, Path] = {}
    built_sboms: dict[str, Path] = {}
    for component_key in component_keys:
        wheel_path, sbom_path = _build_release_component_output(
            runtime,
            repo=repo,
            component_key=component_key,
            dist_root_path=dist_root_path,
            resolved_sbom_path=resolved_sbom_paths[component_key],
            python_exe=python_exe,
            no_isolation=no_isolation,
            validate_wheel_artifact_sbom=validate_wheel_artifact_sbom,
            write_wheel_artifact_sbom=write_wheel_artifact_sbom,
        )
        built_wheels[component_key] = wheel_path
        built_sboms[component_key] = sbom_path
    return built_wheels, built_sboms


def _build_release_component_output(
    runtime: Any,
    *,
    repo: str,
    component_key: str,
    dist_root_path: Path,
    resolved_sbom_path: Path,
    python_exe: str,
    no_isolation: bool,
    validate_wheel_artifact_sbom: Any,
    write_wheel_artifact_sbom: Any,
) -> tuple[Path, Path]:
    """Build the wheel and SBOM for one release component."""
    target = RELEASE_COMPONENT_TARGETS[component_key]
    component = select_components(
        runtime.repo_root,
        named_component=target.source_dir,
    )[0]
    wheel_path = build_component_wheel(
        runtime,
        component=component,
        python_exe=python_exe,
        out_dir=dist_root_path / target.dist_dirname,
        no_isolation=no_isolation,
    )
    sbom_path = write_wheel_artifact_sbom(
        repo_root=runtime.repo_root,
        python_exe=python_exe,
        artifact=wheel_path,
        sbom_path=resolved_sbom_path,
        root_component_name=target.root_component_name,
        repo=repo,
        component_dir=target.source_dir,
    )
    validate_wheel_artifact_sbom(
        artifact=wheel_path,
        sbom_path=sbom_path,
        root_component_name=target.root_component_name,
        repo=repo,
    )
    return wheel_path, sbom_path


def _log_release_build_results(
    runtime: Any,
    *,
    component_keys: list[str],
    built_wheels: dict[str, Path],
    built_sboms: dict[str, Path],
    manual_pdf: Path | None,
) -> None:
    """Log the wheel, SBOM, and manual outputs created by the workflow."""
    runtime.info("SBOM validation complete.")
    runtime.info("Build complete.")
    for component_key in component_keys:
        target = RELEASE_COMPONENT_TARGETS[component_key]
        runtime.info(f"{target.display_name} wheel: {built_wheels[component_key]}")
        runtime.info(f"{target.display_name} SBOM: {built_sboms[component_key]}")
    if manual_pdf is not None:
        runtime.info(f"PDF Manual: {manual_pdf}")


def _publish_release_build_outputs(
    runtime: Any,
    *,
    repo: str,
    tag: str,
    release_name: str | None,
    release_notes: str,
    release_notes_file: str | None,
    draft: bool,
    prerelease: bool,
    github_token: str,
    component_keys: list[str],
    built_wheels: dict[str, Path],
    built_sboms: dict[str, Path],
    manual_pdf: Path | None,
) -> None:
    """Publish built assets to a GitHub release."""
    token = _resolve_github_release_token(github_token)
    notes = _load_release_notes_text(
        release_notes=release_notes,
        release_notes_file=release_notes_file,
    )
    publish_paths = _collect_publish_paths(
        component_keys=component_keys,
        built_wheels=built_wheels,
        built_sboms=built_sboms,
        manual_pdf=manual_pdf,
    )
    _publish_release_assets(
        repo=repo,
        tag=tag,
        release_name=release_name,
        release_notes=notes,
        draft=draft,
        prerelease=prerelease,
        token=token,
        artifact_paths=publish_paths,
        runtime=runtime,
    )
    runtime.info("Publish complete.")


def _resolve_github_release_token(github_token: str) -> str:
    """Resolve the GitHub token used for release publishing."""
    token = (
        github_token.strip()
        or os.environ.get("GITHUB_TOKEN", "").strip()
        or os.environ.get("GH_TOKEN", "").strip()
    )
    if token:
        return token
    raise RuntimeError(
        "GitHub token is required for publish; use --github-token or set GITHUB_TOKEN/GH_TOKEN"
    )


def publish_github_release_files(
    *,
    runtime: Any,
    repo: str,
    tag: str,
    artifact_paths: list[Path],
    github_token: str = "",
    release_name: str | None = None,
    release_notes: str = DEFAULT_RELEASE_NOTES,
    draft: bool = False,
    prerelease: bool = False,
) -> None:
    """Create or reuse a GitHub release and upload local files as assets.

    Parameters
    ----------
    runtime:
        Command runtime used for progress logging.
    repo:
        GitHub repository in ``owner/name`` form.
    tag:
        Release tag to create or update.
    artifact_paths:
        Existing host files uploaded as release assets.
    github_token:
        Explicit token override; ``GITHUB_TOKEN`` and ``GH_TOKEN`` are
        checked when this value is empty.
    release_name:
        Optional display name used when a release must be created.
    release_notes:
        Release body used when a release must be created.
    draft:
        Whether a newly created release should remain a draft.
    prerelease:
        Whether a newly created release should be marked as a prerelease.

    """
    missing_paths = [path for path in artifact_paths if not path.is_file()]
    if missing_paths:
        raise RuntimeError(f"Release asset does not exist: {missing_paths[0]}")
    token = _resolve_github_release_token(github_token)
    _publish_release_assets(
        repo=repo,
        tag=tag,
        release_name=release_name,
        release_notes=release_notes,
        draft=draft,
        prerelease=prerelease,
        token=token,
        artifact_paths=artifact_paths,
        runtime=runtime,
    )
    runtime.info("Publish complete.")


def _collect_publish_paths(
    *,
    component_keys: list[str],
    built_wheels: dict[str, Path],
    built_sboms: dict[str, Path],
    manual_pdf: Path | None,
) -> list[Path]:
    """Collect every artefact path that should be uploaded for a release."""
    publish_paths = [
        path
        for component_key in component_keys
        for path in (built_wheels[component_key], built_sboms[component_key])
    ]
    if manual_pdf is not None:
        publish_paths.append(manual_pdf)
    return publish_paths


def _resolve_repo_path(repo_root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def _refresh_provider_ui_compact_assets(runtime: Any, *, python_exe: str) -> None:
    """Regenerate compacted provider web UI JavaScript assets."""
    del python_exe
    compact_provider_ui_assets(runtime)


def _build_pdf(runtime: Any, *, python_exe: str, output: str) -> None:
    runtime.ensure_python_module(
        python_exe=python_exe,
        module_name="reportlab",
        pip_package="reportlab",
    )
    runtime.run(
        [
            python_exe,
            str(runtime.repo_root / "dev-tools" / "src" / "opamp_dev_tools" / "pdf_manual.py"),
            "--repo-root",
            str(runtime.repo_root),
            "--output",
            output,
        ],
        cwd=runtime.repo_root,
    )


def _github_request(
    *,
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
    content_type: str = "application/json",
) -> Any:
    """Issue one authenticated GitHub API request and return parsed JSON."""
    data: bytes | None = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "opamp-dev-tools-release-assets",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = content_type

    request = urllib.request.Request(  # noqa: S310 - URL is built from the GitHub HTTPS API.
        url, data=data, headers=headers, method=method.upper()
    )
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310  # nosec B310
            raw = response.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {url} failed: {exc.code} {body}") from exc


def _github_upload_asset(
    *,
    upload_url_template: str,
    asset_path: Path,
    token: str,
) -> Any:
    """Upload one release asset to the GitHub uploads API."""
    base_upload_url = upload_url_template.split("{", 1)[0]
    query = urllib.parse.urlencode({"name": asset_path.name})
    url = f"{base_upload_url}?{query}"
    data = asset_path.read_bytes()
    content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
    request = urllib.request.Request(  # noqa: S310 - URL is a GitHub HTTPS upload URL.
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "opamp-dev-tools-release-assets",
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310  # nosec B310
            raw = response.read()
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub asset upload failed for {asset_path.name}: {exc.code} {body}"
        ) from exc


def _release_by_tag(*, repo: str, tag: str, token: str) -> dict[str, Any] | None:
    """Return release JSON for one tag when it exists; otherwise None."""
    url = f"https://api.github.com/repos/{repo}/releases/tags/{urllib.parse.quote(tag)}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "opamp-dev-tools-release-assets",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310  # nosec B310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub release lookup failed: {exc.code} {body}") from exc


def _create_release(
    *,
    repo: str,
    tag: str,
    token: str,
    name: str | None,
    body: str,
    draft: bool,
    prerelease: bool,
) -> dict[str, Any]:
    """Create a GitHub release and return its JSON payload."""
    return _github_request(
        method="POST",
        url=f"https://api.github.com/repos/{repo}/releases",
        token=token,
        payload={
            "tag_name": tag,
            "name": name or tag,
            "body": body,
            "draft": bool(draft),
            "prerelease": bool(prerelease),
        },
    )


def _delete_existing_assets(
    *,
    repo: str,
    release: dict[str, Any],
    token: str,
    asset_names: set[str],
    runtime: Any,
) -> None:
    """Delete same-name assets from a release so re-uploads succeed."""
    for asset in release.get("assets", []):
        name = str(asset.get("name") or "")
        if name not in asset_names:
            continue
        asset_id = asset.get("id")
        if not isinstance(asset_id, int):
            continue
        runtime.info(f"Removing existing release asset: {name}")
        _github_request(
            method="DELETE",
            url=f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}",
            token=token,
        )


def _publish_release_assets(
    *,
    repo: str,
    tag: str,
    release_name: str | None,
    release_notes: str,
    draft: bool,
    prerelease: bool,
    token: str,
    artifact_paths: list[Path],
    runtime: Any,
) -> None:
    """Create or update one release and upload build artefacts as assets."""
    release = _release_by_tag(repo=repo, tag=tag, token=token)
    if release is None:
        runtime.info(f"Creating GitHub release {tag} in {repo}...")
        release = _create_release(
            repo=repo,
            tag=tag,
            token=token,
            name=release_name,
            body=release_notes,
            draft=draft,
            prerelease=prerelease,
        )
    else:
        runtime.info(f"Using existing GitHub release for tag {tag}.")

    _delete_existing_assets(
        repo=repo,
        release=release,
        token=token,
        asset_names={path.name for path in artifact_paths},
        runtime=runtime,
    )

    upload_url = str(release.get("upload_url") or "")
    if not upload_url:
        raise RuntimeError("GitHub release payload missing upload_url")

    for artifact_path in artifact_paths:
        runtime.info(f"Uploading {artifact_path.name}...")
        asset = _github_upload_asset(
            upload_url_template=upload_url,
            asset_path=artifact_path,
            token=token,
        )
        runtime.info(f"Uploaded: {asset.get('browser_download_url', '<no download URL>')}")


def _load_release_notes_text(
    *,
    release_notes: str,
    release_notes_file: str | None,
) -> str:
    """Resolve release notes from CLI options."""
    if release_notes_file:
        return Path(release_notes_file).read_text(encoding="utf-8")
    if release_notes:
        return release_notes
    return DEFAULT_RELEASE_NOTES
