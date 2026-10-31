"""Vendored CycloneDX SBOM helpers for the standalone MCP packaging wheel.

This file intentionally mirrors `dev-tools/src/opamp_dev_tools/sbom.py` from
the source tree so the installed `opamp-mcp-config` wheel stays self-contained
and does not depend on repo-local developer tooling modules.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from email import message_from_bytes
from pathlib import Path
from typing import Any

SBOM_SCHEMA_URL = "http://cyclonedx.org/schema/bom-1.6.schema.json"
SBOM_FORMAT = "CycloneDX"
SBOM_SPEC_VERSION = "1.6"
SBOM_VERSION = 1
JSON_INDENT = 2
UTF8_ENCODING = "utf-8"
LICENSE_ID_APACHE_2 = "Apache-2.0"
HASH_ALGORITHM_SHA256 = "SHA-256"
PYPI_PURL_PREFIX = "pkg:pypi"
REQUIREMENT_MARKER_EXTRA = "extra =="
TIMESTAMP_Z_SUFFIX_FROM = "+00:00"
TIMESTAMP_Z_SUFFIX_TO = "Z"


def _run(command: list[str], *, cwd: Path) -> None:
    """Run one internally assembled package command and stream its output.

    Parameters
    ----------
    command:
        Argument vector built by the trusted SBOM packaging workflow.
    cwd:
        Working directory in which the command should run.

    """
    print(f"+ {' '.join(command)}")
    # The caller builds command arguments from fixed packaging operations, without a shell.
    subprocess.run(command, cwd=str(cwd), check=True)  # noqa: S603


def ensure_python_package(
    *,
    repo_root: Path,
    python_exe: str,
    package_name: str,
) -> None:
    """Ensure a Python package is available in the active environment.

    Parameters
    ----------
    repo_root:
        Repository root used as the package-command working directory.
    python_exe:
        Selected Python interpreter path.
    package_name:
        Trusted packaging dependency to locate or install.

    """
    # The interpreter and package are supplied by the trusted packaging workflow.
    probe = subprocess.run(  # noqa: S603
        [python_exe, "-m", "pip", "show", package_name],
        cwd=str(repo_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode == 0:
        return
    print(f"Python package `{package_name}` not found; installing it now...")
    _run([python_exe, "-m", "pip", "install", package_name], cwd=repo_root)


def normalize_dist_name(value: str) -> str:
    """Normalize a distribution name to a stable lowercase key."""
    return str(value or "").strip().lower().replace("_", "-")


def sha256(path: Path) -> str:
    """Return SHA-256 digest for one file."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_wheel_metadata(wheel_path: Path) -> dict[str, Any]:
    """Read Name/Version/Requires-Dist from a wheel METADATA payload."""
    metadata_bytes: bytes | None = None
    with zipfile.ZipFile(wheel_path, "r") as archive:
        for member in archive.namelist():
            if member.endswith(".dist-info/METADATA"):
                metadata_bytes = archive.read(member)
                break
    if metadata_bytes is None:
        raise RuntimeError(f"wheel missing dist-info/METADATA: {wheel_path}")

    metadata = message_from_bytes(metadata_bytes)
    name = str(metadata.get("Name") or wheel_path.stem).strip()
    version = str(metadata.get("Version") or "0").strip()
    requires_dist = [str(item).strip() for item in metadata.get_all("Requires-Dist") or []]
    return {"name": name, "version": version, "requires_dist": requires_dist}


def requirement_name(requirement: str) -> str:
    """Extract dependency package name from a `Requires-Dist` entry."""
    cleaned = requirement.split(";", 1)[0].strip()
    stop_chars = [" ", "(", "[", "!", "<", ">", "=", "~", ";"]
    end = len(cleaned)
    for char in stop_chars:
        pos = cleaned.find(char)
        if pos != -1:
            end = min(end, pos)
    return cleaned[:end].strip()


def expected_dependency_refs(requires_dist: list[str]) -> list[str]:
    """Return normalized CycloneDX dependency refs for non-extra requirements."""
    dep_refs: set[str] = set()
    for requirement in requires_dist:
        if REQUIREMENT_MARKER_EXTRA in requirement.lower():
            continue
        dep_name = requirement_name(requirement)
        if dep_name:
            dep_refs.add(f"{PYPI_PURL_PREFIX}/{normalize_dist_name(dep_name)}")
    return sorted(dep_refs)


def parse_iso8601_utc(value: str) -> datetime | None:
    """Parse an ISO-8601 timestamp into UTC datetime when possible."""
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_component_refs(sbom: dict[str, Any]) -> list[str]:
    components = sbom.get("components")
    if not isinstance(components, list):
        sbom["components"] = []
        return []

    dep_refs: list[str] = []
    for component in components:
        if not isinstance(component, dict):
            continue
        purl = str(component.get("purl") or "").strip()
        if purl.startswith(f"{PYPI_PURL_PREFIX}/"):
            component["bom-ref"] = purl
            dep_refs.append(purl)
    return sorted(set(dep_refs))


def _build_base_requirements_sbom(
    *,
    repo_root: Path,
    python_exe: str,
    requirements: list[str],
    cwd: Path | None = None,
) -> dict[str, Any]:
    ensure_python_package(
        repo_root=repo_root,
        python_exe=python_exe,
        package_name="cyclonedx-bom",
    )
    with tempfile.TemporaryDirectory(prefix="opamp-sbom-") as temp_dir:
        temp_root = Path(temp_dir)
        requirements_path = temp_root / "requirements.txt"
        requirements_path.write_text(
            "".join(f"{requirement}\n" for requirement in requirements),
            encoding=UTF8_ENCODING,
        )
        intermediate_output = temp_root / "sbom.json"
        _run(
            [
                python_exe,
                "-m",
                "cyclonedx_py",
                "requirements",
                str(requirements_path),
                "--output-format",
                "JSON",
                "--spec-version",
                SBOM_SPEC_VERSION,
                "--output-file",
                str(intermediate_output),
            ],
            cwd=cwd or repo_root,
        )
        payload = json.loads(intermediate_output.read_text(encoding=UTF8_ENCODING))
    if not isinstance(payload, dict):
        raise RuntimeError("CycloneDX generation returned invalid SBOM payload.")
    return payload


def build_requirements_application_sbom_payload(  # pylint: disable=too-many-arguments
    *,
    repo_root: Path,
    python_exe: str,
    requirements: list[str],
    root_component_name: str,
    root_component_version: str,
    root_properties: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Build a root-application SBOM payload from a requirements list."""
    sbom = _build_base_requirements_sbom(
        repo_root=repo_root,
        python_exe=python_exe,
        requirements=requirements,
        cwd=cwd,
    )
    dependency_refs = _normalize_component_refs(sbom)
    normalized_root_name = normalize_dist_name(root_component_name)
    root_ref = f"{PYPI_PURL_PREFIX}/{normalized_root_name}@{root_component_version}"
    root_component: dict[str, Any] = {
        "type": "application",
        "name": str(root_component_name).strip(),
        "version": str(root_component_version).strip(),
        "bom-ref": root_ref,
        "purl": root_ref,
        "licenses": [{"license": {"id": LICENSE_ID_APACHE_2}}],
    }
    if root_properties:
        root_component["properties"] = [
            {"name": name, "value": value}
            for name, value in sorted(root_properties.items())
            if str(value).strip()
        ]

    metadata = sbom.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata["component"] = root_component
    sbom["metadata"] = metadata

    components = sbom.get("components")
    if not isinstance(components, list):
        components = []
    components = [component for component in components if isinstance(component, dict)]
    components = [root_component] + [
        component
        for component in components
        if str(component.get("bom-ref") or "").strip() != root_ref
    ]
    sbom["components"] = components

    dependencies = sbom.get("dependencies")
    if not isinstance(dependencies, list):
        dependencies = []
    dependencies = [entry for entry in dependencies if isinstance(entry, dict)]
    dependencies = [
        entry
        for entry in dependencies
        if str(entry.get("ref") or "").strip() != root_ref
    ]
    dependencies.insert(0, {"ref": root_ref, "dependsOn": dependency_refs})
    sbom["dependencies"] = dependencies
    return sbom


def build_wheel_artifact_sbom_payload(  # pylint: disable=too-many-arguments,too-many-locals
    *,
    repo_root: Path,
    python_exe: str,
    artifact: Path,
    root_component_name: str,
    root_component_version: str | None = None,
    repo: str | None = None,
    component_dir: str | None = None,
    metadata_component_mode: str = "root",
) -> dict[str, Any]:
    """Build a CycloneDX payload for one wheel artifact."""
    del repo_root
    del python_exe

    wheel_meta = read_wheel_metadata(artifact)
    name = str(wheel_meta["name"])
    version = str(wheel_meta["version"])
    bom_ref = f"{PYPI_PURL_PREFIX}/{normalize_dist_name(name)}@{version}"

    dependency_names = sorted(
        {
            requirement_name(requirement)
            for requirement in wheel_meta["requires_dist"]
            if REQUIREMENT_MARKER_EXTRA not in requirement.lower()
            and requirement_name(requirement)
        }
    )
    dependency_refs = [
        f"{PYPI_PURL_PREFIX}/{normalize_dist_name(dependency_name)}"
        for dependency_name in dependency_names
    ]

    wheel_component: dict[str, Any] = {
        "type": "library",
        "name": name,
        "version": version,
        "bom-ref": bom_ref,
        "purl": bom_ref,
        "hashes": [{"alg": HASH_ALGORITHM_SHA256, "content": sha256(artifact)}],
        "licenses": [{"license": {"id": LICENSE_ID_APACHE_2}}],
        "properties": [{"name": "opamp.artifact.path", "value": str(artifact)}],
        "externalReferences": [
            {
                "type": "distribution",
                "url": artifact.resolve().as_uri(),
            }
        ],
    }
    dependency_components = [
        {
            "type": "library",
            "name": dependency_name,
            "bom-ref": dependency_ref,
            "purl": dependency_ref,
        }
        for dependency_name, dependency_ref in zip(
            dependency_names,
            dependency_refs,
            strict=True,
        )
    ]

    metadata_component: dict[str, Any]
    if metadata_component_mode == "artifact":
        metadata_component = wheel_component
    else:
        metadata_properties: list[dict[str, str]] = [
            {"name": "wheel.name", "value": name},
        ]
        if repo:
            metadata_properties.append({"name": "github.repository", "value": repo})
        if component_dir:
            metadata_properties.append(
                {"name": "component.directory", "value": component_dir}
            )
        metadata_component = {
            "type": "application",
            "name": root_component_name,
            "version": str(root_component_version or version).strip(),
            "properties": metadata_properties,
        }

    return {
        "$schema": SBOM_SCHEMA_URL,
        "bomFormat": SBOM_FORMAT,
        "specVersion": SBOM_SPEC_VERSION,
        "version": SBOM_VERSION,
        "metadata": {
            "timestamp": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace(TIMESTAMP_Z_SUFFIX_FROM, TIMESTAMP_Z_SUFFIX_TO),
            "component": metadata_component,
        },
        "components": [wheel_component] + dependency_components,
        "dependencies": [{"ref": bom_ref, "dependsOn": dependency_refs}],
    }


def write_sbom_file(payload: dict[str, Any], output_path: Path) -> Path:
    """Write one SBOM JSON document to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=JSON_INDENT) + "\n",
        encoding=UTF8_ENCODING,
    )
    return output_path


def write_wheel_artifact_sbom(  # pylint: disable=too-many-arguments
    *,
    repo_root: Path,
    python_exe: str,
    artifact: Path,
    sbom_path: Path,
    root_component_name: str,
    root_component_version: str | None = None,
    repo: str | None = None,
    component_dir: str | None = None,
    metadata_component_mode: str = "root",
) -> Path:
    """Build and write one wheel-artifact SBOM document."""
    payload = build_wheel_artifact_sbom_payload(
        repo_root=repo_root,
        python_exe=python_exe,
        artifact=artifact,
        root_component_name=root_component_name,
        root_component_version=root_component_version,
        repo=repo,
        component_dir=component_dir,
        metadata_component_mode=metadata_component_mode,
    )
    return write_sbom_file(payload, sbom_path)


def _property_value(properties: Any, name: str) -> str | None:
    if not isinstance(properties, list):
        return None
    for entry in properties:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("name") or "").strip() != name:
            continue
        value = entry.get("value")
        return str(value).strip() if value is not None else ""
    return None


def validate_wheel_artifact_sbom(  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    *,
    artifact: Path,
    sbom_path: Path,
    root_component_name: str,
    repo: str | None = None,
) -> None:
    """Fail when a generated SBOM is stale or mismatched to its wheel."""
    if not artifact.exists():
        raise RuntimeError(f"SBOM validation failed: wheel artifact not found: {artifact}")
    if not sbom_path.exists():
        raise RuntimeError(f"SBOM validation failed: SBOM file not found: {sbom_path}")

    try:
        sbom = json.loads(sbom_path.read_text(encoding=UTF8_ENCODING))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"SBOM validation failed: invalid JSON in {sbom_path}: {exc}"
        ) from exc
    if not isinstance(sbom, dict):
        raise RuntimeError(f"SBOM validation failed: root JSON must be an object: {sbom_path}")

    wheel_meta = read_wheel_metadata(artifact)
    wheel_name = str(wheel_meta["name"])
    wheel_version = str(wheel_meta["version"])
    wheel_ref = f"{PYPI_PURL_PREFIX}/{normalize_dist_name(wheel_name)}@{wheel_version}"
    wheel_sha = sha256(artifact)
    expected_dep_refs = expected_dependency_refs(list(wheel_meta["requires_dist"]))
    skew_allowance = timedelta(seconds=5)
    artifact_mtime_utc = datetime.fromtimestamp(artifact.stat().st_mtime, tz=timezone.utc)
    sbom_mtime_utc = datetime.fromtimestamp(sbom_path.stat().st_mtime, tz=timezone.utc)

    if sbom_mtime_utc + skew_allowance < artifact_mtime_utc:
        raise RuntimeError(
            "SBOM validation failed: SBOM file timestamp is older than wheel artifact; "
            f"regeneration required ({sbom_path} vs {artifact})."
        )

    metadata = sbom.get("metadata")
    if not isinstance(metadata, dict):
        raise RuntimeError("SBOM validation failed: missing/invalid metadata block.")

    timestamp_utc = parse_iso8601_utc(str(metadata.get("timestamp") or ""))
    if timestamp_utc is None:
        raise RuntimeError(
            "SBOM validation failed: metadata.timestamp missing or invalid ISO-8601."
        )
    if timestamp_utc + skew_allowance < artifact_mtime_utc:
        raise RuntimeError(
            "SBOM validation failed: metadata.timestamp predates wheel artifact "
            f"({timestamp_utc.isoformat()} < {artifact_mtime_utc.isoformat()})."
        )

    metadata_component = metadata.get("component")
    if not isinstance(metadata_component, dict):
        raise RuntimeError("SBOM validation failed: metadata.component is missing.")
    if str(metadata_component.get("name") or "").strip() != root_component_name:
        raise RuntimeError(
            "SBOM validation failed: unexpected metadata.component.name "
            f"(expected {root_component_name!r})."
        )
    metadata_version = str(metadata_component.get("version") or "").strip()
    if metadata_version and metadata_version != wheel_version:
        raise RuntimeError(
            "SBOM validation failed: metadata.component.version does not match wheel version."
        )
    metadata_repository = _property_value(
        metadata_component.get("properties"),
        "github.repository",
    )
    if repo is not None and metadata_repository != repo:
        raise RuntimeError(
            "SBOM validation failed: metadata github.repository does not match build target."
        )
    metadata_wheel_name = _property_value(metadata_component.get("properties"), "wheel.name")
    if metadata_wheel_name is not None and metadata_wheel_name != wheel_name:
        raise RuntimeError("SBOM validation failed: metadata wheel.name does not match wheel.")

    components = sbom.get("components")
    if not isinstance(components, list):
        raise RuntimeError("SBOM validation failed: components list is missing/invalid.")
    wheel_component = None
    for component in components:
        if not isinstance(component, dict):
            continue
        if str(component.get("bom-ref") or "").strip() == wheel_ref:
            wheel_component = component
            break
    if wheel_component is None:
        raise RuntimeError(
            "SBOM validation failed: wheel component entry not found in components."
        )

    hash_content: str | None = None
    hashes = wheel_component.get("hashes")
    if isinstance(hashes, list):
        for item in hashes:
            if not isinstance(item, dict):
                continue
            if str(item.get("alg") or "").strip().upper() == HASH_ALGORITHM_SHA256:
                value = item.get("content")
                hash_content = str(value).strip() if value is not None else ""
                break
    if hash_content != wheel_sha:
        raise RuntimeError(
            "SBOM validation failed: wheel SHA-256 hash in SBOM does not match artifact."
        )

    expected_path = str(artifact)
    sbom_artifact_path = _property_value(wheel_component.get("properties"), "opamp.artifact.path")
    if sbom_artifact_path != expected_path:
        raise RuntimeError(
            "SBOM validation failed: wheel artifact path in SBOM does not match built artifact."
        )

    dependencies = sbom.get("dependencies")
    if not isinstance(dependencies, list):
        raise RuntimeError("SBOM validation failed: dependencies list is missing/invalid.")
    dependency_entry = None
    for entry in dependencies:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("ref") or "").strip() == wheel_ref:
            dependency_entry = entry
            break
    if dependency_entry is None:
        raise RuntimeError("SBOM validation failed: dependencies entry for wheel is missing.")

    depends_on = dependency_entry.get("dependsOn")
    if not isinstance(depends_on, list):
        raise RuntimeError("SBOM validation failed: dependencies.ref.dependsOn is invalid.")
    actual_dep_refs = sorted({str(item).strip() for item in depends_on if str(item).strip()})
    if actual_dep_refs != expected_dep_refs:
        raise RuntimeError(
            "SBOM validation failed: dependency refs do not match wheel metadata requirements."
        )
