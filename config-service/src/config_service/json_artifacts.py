#!/usr/bin/env python3
# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from config_service.json_utils import JsonConfigLoadError, load_json_file

UTF8_ENCODING = "utf-8"
KEY_ARTIFACT_MANIFEST = "artifact_manifest"
KEY_FORMAT = "format"
KEY_BASE = "base"
KEY_PARTS = "parts"
KEY_POINTER = "pointer"
KEY_FILE = "file"
KEY_OPERATION = "operation"
KEY_PAYLOAD = "payload"
KEY_REF = "$ref"
MANIFEST_FORMAT_V1 = "config-service.composite-json/v1"
OPERATION_REPLACE = "replace"
OPERATION_APPEND = "append"
SUPPORTED_OPERATIONS = {OPERATION_REPLACE, OPERATION_APPEND}


class JsonArtifactError(ValueError):
    """Raised when a composite JSON artifact manifest is invalid."""


def load_json_artifact(path: Path) -> Any:
    """Load one JSON artifact, assembling it when the file is a manifest."""
    try:
        payload = load_json_file(path, purpose="JSON artifact")
    except JsonConfigLoadError as exc:
        raise JsonArtifactError(str(exc)) from exc
    if not _is_manifest(payload):
        return payload
    return _assemble_manifest(path, payload, loader=load_json_artifact)


def load_json_schema_artifact(path: Path) -> Any:
    """Load one JSON Schema artifact, resolving manifests and file `$ref`s."""
    try:
        payload = load_json_file(path, purpose="JSON schema artifact")
    except JsonConfigLoadError as exc:
        raise JsonArtifactError(str(exc)) from exc
    if _is_manifest(payload):
        return _assemble_manifest(path, payload, loader=load_json_schema_artifact)
    return _resolve_json_schema_refs(payload, source_path=path, root_document=payload, root_path=path)


def write_split_json_artifact(
    path: Path,
    payload: Any,
    *,
    split_parts: list[tuple[str, str]],
) -> None:
    """Write one payload as a manifest plus externalized base/part files."""
    if not split_parts:
        _write_json(path, payload)
        return

    base_payload = copy.deepcopy(payload)
    manifest_parts: list[dict[str, Any]] = []
    written_files: set[Path] = {path}
    for pointer, label in split_parts:
        part_payload = _pop_pointer(base_payload, pointer)
        part_path = _derived_artifact_path(path, label)
        _write_json(part_path, part_payload)
        manifest_parts.append(
            {
                KEY_POINTER: pointer,
                KEY_FILE: part_path.name,
                KEY_PAYLOAD: part_payload,
            }
        )
        written_files.add(part_path)

    base_path = _derived_artifact_path(path, "base")
    write_manifest_json_artifact(
        path,
        base_file=base_path.name,
        base_payload=base_payload,
        parts=manifest_parts,
    )
    written_files.add(base_path)

    for stale_path in path.parent.glob(f"{path.stem}.*{path.suffix}"):
        if stale_path not in written_files:
            stale_path.unlink(missing_ok=True)


def write_manifest_json_artifact(
    path: Path,
    *,
    base_file: str,
    base_payload: Any,
    parts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Write one JSON manifest with explicit base and part payloads."""
    base_path = path.parent / Path(base_file)
    _write_json(base_path, base_payload)

    manifest_parts: list[dict[str, str]] = []
    for index, part in enumerate(parts):
        if not isinstance(part, dict):
            raise JsonArtifactError(f"Manifest write part[{index}] must be an object")
        pointer = str(part.get(KEY_POINTER) or "")
        file_name = str(part.get(KEY_FILE) or "").strip()
        operation = str(part.get(KEY_OPERATION) or OPERATION_REPLACE)
        if not pointer or not file_name:
            raise JsonArtifactError(f"Manifest write part[{index}] requires pointer and file")
        if operation not in SUPPORTED_OPERATIONS:
            raise JsonArtifactError(f"Unsupported manifest write operation '{operation}'")

        part_path = path.parent / Path(file_name)
        _write_json(part_path, part.get(KEY_PAYLOAD))

        manifest_part = {KEY_POINTER: pointer, KEY_FILE: file_name.replace("\\", "/")}
        if operation != OPERATION_REPLACE:
            manifest_part[KEY_OPERATION] = operation
        manifest_parts.append(manifest_part)

    manifest_payload = {
        KEY_ARTIFACT_MANIFEST: {
            KEY_FORMAT: MANIFEST_FORMAT_V1,
            KEY_BASE: str(Path(base_file)).replace("\\", "/"),
            KEY_PARTS: manifest_parts,
        }
    }
    _write_json(path, manifest_payload)
    return manifest_payload


def _is_manifest(payload: Any) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get(KEY_ARTIFACT_MANIFEST), dict)


def _assemble_manifest(path: Path, payload: dict[str, Any], *, loader: Any) -> Any:
    manifest = payload.get(KEY_ARTIFACT_MANIFEST, {})
    if str(manifest.get(KEY_FORMAT) or "") != MANIFEST_FORMAT_V1:
        raise JsonArtifactError(f"Unsupported artifact manifest format in {path}")

    base_name = str(manifest.get(KEY_BASE) or "").strip()
    if not base_name:
        raise JsonArtifactError(f"Manifest base is required in {path}")

    base_path = path.parent / base_name
    assembled = loader(base_path)
    if not isinstance(manifest.get(KEY_PARTS), list):
        raise JsonArtifactError(f"Manifest parts must be a list in {path}")

    for index, part in enumerate(manifest.get(KEY_PARTS, [])):
        if not isinstance(part, dict):
            raise JsonArtifactError(f"Manifest part[{index}] must be an object in {path}")
        pointer = str(part.get(KEY_POINTER) or "")
        file_name = str(part.get(KEY_FILE) or "").strip()
        operation = str(part.get(KEY_OPERATION) or OPERATION_REPLACE)
        if not pointer or not file_name:
            raise JsonArtifactError(f"Manifest part[{index}] requires pointer and file in {path}")
        if operation not in SUPPORTED_OPERATIONS:
            raise JsonArtifactError(f"Unsupported manifest operation '{operation}' in {path}")
        part_payload = loader(path.parent / file_name)
        _set_pointer(assembled, pointer, part_payload, operation=operation)
    return assembled


def _derived_artifact_path(path: Path, label: str) -> Path:
    derived = path.with_name(f"{path.stem}.{label}{path.suffix}")
    derived.parent.mkdir(parents=True, exist_ok=True)
    return derived


def _pointer_segments(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise JsonArtifactError(f"JSON pointer must start with '/': {pointer}")
    return [segment.replace("~1", "/").replace("~0", "~") for segment in pointer[1:].split("/")]


def _resolve_pointer(payload: Any, pointer: str) -> Any:
    container = payload
    for segment in _pointer_segments(pointer):
        if isinstance(container, dict):
            if segment not in container:
                raise JsonArtifactError(f"JSON pointer not found while assembling manifest: {pointer}")
            container = container[segment]
            continue
        if isinstance(container, list):
            index = _list_index(segment, pointer=pointer, max_index=len(container) - 1)
            container = container[index]
            continue
        raise JsonArtifactError(f"JSON pointer parent must be a container: {pointer}")
    return container


def _set_pointer(payload: Any, pointer: str, value: Any, *, operation: str = OPERATION_REPLACE) -> None:
    if operation == OPERATION_APPEND:
        target = _resolve_pointer(payload, pointer)
        if not isinstance(target, list):
            raise JsonArtifactError(f"JSON pointer append target must be an array: {pointer}")
        target.append(value)
        return

    segments = _pointer_segments(pointer)
    if not segments:
        raise JsonArtifactError("Cannot assign to the root JSON pointer")

    parent_pointer = "/" + "/".join(_escape_pointer_segment(segment) for segment in segments[:-1]) if len(segments) > 1 else ""
    container = payload if not parent_pointer else _resolve_pointer(payload, parent_pointer)
    leaf = segments[-1]

    if isinstance(container, dict):
        container[leaf] = value
        return
    if isinstance(container, list):
        if leaf == "-":
            container.append(value)
            return
        index = _list_index(leaf, pointer=pointer, max_index=len(container), allow_end=True)
        if index == len(container):
            container.append(value)
            return
        container[index] = value
        return
    raise JsonArtifactError(f"JSON pointer parent must be a container: {pointer}")


def _pop_pointer(payload: Any, pointer: str) -> Any:
    segments = _pointer_segments(pointer)
    if not segments:
        raise JsonArtifactError("Cannot remove the root JSON pointer")

    parent_pointer = "/" + "/".join(_escape_pointer_segment(segment) for segment in segments[:-1]) if len(segments) > 1 else ""
    container = payload if not parent_pointer else _resolve_pointer(payload, parent_pointer)
    leaf = segments[-1]

    if isinstance(container, dict):
        if leaf not in container:
            raise JsonArtifactError(f"JSON pointer not found while splitting artifact: {pointer}")
        return container.pop(leaf)
    if isinstance(container, list):
        index = _list_index(leaf, pointer=pointer, max_index=len(container) - 1)
        return container.pop(index)
    raise JsonArtifactError(f"JSON pointer parent must be a container: {pointer}")


def _list_index(segment: str, *, pointer: str, max_index: int, allow_end: bool = False) -> int:
    try:
        index = int(segment)
    except ValueError as exc:
        raise JsonArtifactError(f"JSON pointer array segment must be an integer: {pointer}") from exc
    limit = max_index if not allow_end else max_index
    if index < 0 or index > limit:
        raise JsonArtifactError(f"JSON pointer array index out of range: {pointer}")
    return index


def _escape_pointer_segment(segment: str) -> str:
    return segment.replace("~", "~0").replace("/", "~1")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding=UTF8_ENCODING)


def _resolve_json_schema_refs(
    payload: Any,
    *,
    source_path: Path,
    root_document: Any,
    root_path: Path,
    seen: set[tuple[Path, str]] | None = None,
) -> Any:
    seen_refs = seen if seen is not None else set()
    if isinstance(payload, dict):
        ref_value = payload.get(KEY_REF)
        if isinstance(ref_value, str):
            resolved = _load_json_schema_ref(
                ref_value,
                source_path=source_path,
                root_document=root_document,
                root_path=root_path,
                seen=seen_refs,
            )
            sibling_items = {key: value for key, value in payload.items() if key != KEY_REF}
            if sibling_items:
                if not isinstance(resolved, dict):
                    raise JsonArtifactError(
                        f"Cannot merge JSON Schema $ref siblings into non-object target: {source_path}"
                    )
                merged = copy.deepcopy(resolved)
                for key, value in sibling_items.items():
                    merged[key] = _resolve_json_schema_refs(
                        value,
                        source_path=source_path,
                        root_document=root_document,
                        root_path=root_path,
                        seen=seen_refs,
                    )
                return merged
            return resolved
        return {
            key: _resolve_json_schema_refs(
                value,
                source_path=source_path,
                root_document=root_document,
                root_path=root_path,
                seen=seen_refs,
            )
            for key, value in payload.items()
        }
    if isinstance(payload, list):
        return [
            _resolve_json_schema_refs(
                item,
                source_path=source_path,
                root_document=root_document,
                root_path=root_path,
                seen=seen_refs,
            )
            for item in payload
        ]
    return payload


def _load_json_schema_ref(
    ref: str,
    *,
    source_path: Path,
    root_document: Any,
    root_path: Path,
    seen: set[tuple[Path, str]],
) -> Any:
    file_part, fragment = _split_json_schema_ref(ref)
    if file_part:
        target_path = (source_path.parent / file_part).resolve()
        ref_key = (target_path, fragment)
        if ref_key in seen:
            raise JsonArtifactError(f"Cyclic JSON Schema $ref detected: {ref}")
        seen.add(ref_key)
        target_document = load_json_schema_artifact(target_path)
        target_root = target_path
        resolved = _resolve_json_schema_pointer(target_document, fragment, target_path=target_path)
        seen.remove(ref_key)
        return resolved

    ref_key = (root_path.resolve(), fragment)
    if ref_key in seen:
        raise JsonArtifactError(f"Cyclic JSON Schema $ref detected: {ref}")
    seen.add(ref_key)
    resolved = _resolve_json_schema_pointer(root_document, fragment, target_path=root_path)
    seen.remove(ref_key)
    return _resolve_json_schema_refs(
        resolved,
        source_path=root_path,
        root_document=root_document,
        root_path=root_path,
        seen=seen,
    )


def _split_json_schema_ref(ref: str) -> tuple[str, str]:
    if "#" not in ref:
        return ref, ""
    file_part, fragment = ref.split("#", 1)
    return file_part, fragment


def _resolve_json_schema_pointer(document: Any, fragment: str, *, target_path: Path) -> Any:
    if fragment == "":
        return copy.deepcopy(document)
    pointer = unquote(fragment)
    if not pointer.startswith("/"):
        raise JsonArtifactError(f"Unsupported JSON Schema ref fragment in {target_path}: #{fragment}")
    return copy.deepcopy(_resolve_pointer(document, pointer))
