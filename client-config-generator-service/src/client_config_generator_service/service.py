# Copyright 2026 mp3monster.org
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

"""Schema validation and safe file persistence for generated client configs."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CONFIGURATION_EXTENSION = ".json"
KEY_CONFIGURATION = "configuration"
KEY_ERRORS = "errors"
KEY_MESSAGE = "message"
KEY_PATH = "path"
KEY_VALID = "valid"


class ConfigurationFileService:
    """Lists, validates, reads, and atomically writes consumer JSON configurations."""

    def __init__(self, *, root_directory: Path, schema_path: Path, read_only: bool) -> None:
        """Initialize storage and schema validation.

        Args:
            root_directory: Only directory in which configuration files may be accessed.
            schema_path: Bundled JSON Schema used for validation and UI generation.
            read_only: When true, save operations are rejected.
        """
        self.root_directory = root_directory.resolve()
        # ``schema_path`` identifies the immutable definition served to the UI.
        self.schema_path = schema_path.resolve()
        # ``read_only`` controls whether save requests may mutate files.
        self.read_only = read_only
        self.root_directory.mkdir(parents=True, exist_ok=True)
        self.schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(self.schema)

    def list_configurations(self) -> list[str]:
        """Return sorted relative paths for available JSON configurations."""
        return sorted(
            path.relative_to(self.root_directory).as_posix()
            for path in self.root_directory.rglob(f"*{CONFIGURATION_EXTENSION}")
            if path.is_file()
        )

    def resolve_configuration_path(self, relative_name: str) -> Path:
        """Resolve and validate one user-provided JSON file name.

        Args:
            relative_name: Relative path supplied by an API caller.
        """
        normalized_name = str(relative_name or "").strip().replace("\\", "/")
        if not normalized_name or not normalized_name.lower().endswith(CONFIGURATION_EXTENSION):
            raise ValueError("configuration name must end with .json")
        candidate_path = (self.root_directory / normalized_name).resolve()
        try:
            candidate_path.relative_to(self.root_directory)
        except ValueError as error:
            raise ValueError(
                "configuration path must remain inside the configured directory"
            ) from error
        return candidate_path

    def load_configuration(self, relative_name: str) -> dict[str, Any]:
        """Load a selected consumer configuration JSON object.

        Args:
            relative_name: Relative JSON file name within the configured directory.
        """
        configuration_path = self.resolve_configuration_path(relative_name)
        payload = json.loads(configuration_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("configuration file must contain a JSON object")
        return payload

    def validate_configuration(self, configuration: Any) -> dict[str, Any]:
        """Validate a candidate payload and return stable field-level errors.

        Args:
            configuration: Candidate root consumer configuration payload.
        """
        validation_errors = []
        for validation_error in sorted(
            self.validator.iter_errors(configuration),
            key=lambda error: list(error.absolute_path),
        ):
            field_path = ".".join(str(part) for part in validation_error.absolute_path)
            validation_errors.append(
                {
                    KEY_PATH: field_path,
                    KEY_MESSAGE: validation_error.message,
                }
            )
        return {
            KEY_VALID: not validation_errors,
            KEY_ERRORS: validation_errors,
        }

    def save_configuration(self, relative_name: str, configuration: Any) -> Path:
        """Validate and atomically persist a selected consumer configuration.

        Args:
            relative_name: Relative target JSON file name.
            configuration: Candidate payload to validate and write.
        """
        if self.read_only:
            raise PermissionError("client config generator is read-only")
        validation_result = self.validate_configuration(configuration)
        if validation_result[KEY_VALID] is not True:
            raise ValueError(json.dumps(validation_result[KEY_ERRORS]))

        configuration_path = self.resolve_configuration_path(relative_name)
        configuration_path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=str(configuration_path.parent),
            prefix=f".{configuration_path.name}.",
            suffix=".tmp",
            text=True,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(configuration, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.replace(configuration_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
        return configuration_path
