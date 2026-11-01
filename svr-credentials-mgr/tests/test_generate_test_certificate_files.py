# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Test generation of PEM-style certificate upload fixtures."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_script_module():
    """Load the script module directly from disk for focused unit testing."""
    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "generate_test_certificate_files.py"
    )
    module_spec = importlib.util.spec_from_file_location(
        "generate_test_certificate_files_script",
        script_path,
    )
    assert module_spec is not None
    assert module_spec.loader is not None
    script_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(script_module)
    return script_module


def test_generate_test_certificate_files_with_explicit_prefix(tmp_path: Path) -> None:
    """The helper should create the expected files using the supplied prefix."""
    script_module = load_script_module()
    generated_files = script_module.generate_test_certificate_files(
        tmp_path,
        "demo-client",
    )
    assert sorted(generated_files.keys()) == sorted(script_module.ROLE_TO_FILENAME.keys())
    for file_role, destination_path in generated_files.items():
        assert destination_path.exists()
        assert destination_path.name.startswith("demo-client-")
        pem_text = destination_path.read_text(encoding=script_module.TEXT_ENCODING)
        assert f"BEGIN {script_module.ROLE_TO_PEM_LABEL[file_role]}" in pem_text
        assert f"END {script_module.ROLE_TO_PEM_LABEL[file_role]}" in pem_text


def test_generate_test_certificate_files_uses_timestamp_prefix_when_omitted(
    tmp_path: Path,
) -> None:
    """The helper should generate a readable timestamp prefix when none is supplied."""
    script_module = load_script_module()
    generated_files = script_module.generate_test_certificate_files(tmp_path)
    generated_prefixes = set()
    for file_role, destination_path in generated_files.items():
        suffix = f"-{script_module.ROLE_TO_FILENAME[file_role]}"
        generated_prefixes.add(destination_path.name.removesuffix(suffix))
    assert len(generated_prefixes) == 1
    generated_prefix = next(iter(generated_prefixes))
    assert "_" in generated_prefix
    assert "-" in generated_prefix
