# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

"""Generate PEM-style test certificate and key files for UI upload testing."""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT_DIRECTORY = "test-certs"
DEFAULT_PREFIX_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"
TEXT_ENCODING = "utf-8"
PEM_LINE_LENGTH = 64
PREFIX_SANITIZE_PATTERN = r"[^A-Za-z0-9._-]+"
PEM_CERTIFICATE_LABEL = "CERTIFICATE"
PEM_PRIVATE_KEY_LABEL = "PRIVATE KEY"
PEM_PUBLIC_KEY_LABEL = "PUBLIC KEY"
FILE_ROLE_CERTIFICATE = "certificate"
FILE_ROLE_MOCK_CA_CERTIFICATE = "mock-ca-certificate"
FILE_ROLE_PRIVATE_KEY = "private-key"
FILE_ROLE_PUBLIC_KEY = "public-key"
FILE_ROLE_TLS_CA = "tls-ca"
ROLE_TO_FILENAME = {
    FILE_ROLE_CERTIFICATE: "certificate.pem",
    FILE_ROLE_MOCK_CA_CERTIFICATE: "mock-ca-certificate.pem",
    FILE_ROLE_PRIVATE_KEY: "private-key.key",
    FILE_ROLE_PUBLIC_KEY: "public-key.pub",
    FILE_ROLE_TLS_CA: "tls-ca.pem",
}
ROLE_TO_PEM_LABEL = {
    FILE_ROLE_CERTIFICATE: PEM_CERTIFICATE_LABEL,
    FILE_ROLE_MOCK_CA_CERTIFICATE: PEM_CERTIFICATE_LABEL,
    FILE_ROLE_PRIVATE_KEY: PEM_PRIVATE_KEY_LABEL,
    FILE_ROLE_PUBLIC_KEY: PEM_PUBLIC_KEY_LABEL,
    FILE_ROLE_TLS_CA: PEM_CERTIFICATE_LABEL,
}


def sanitize_prefix(file_prefix: str) -> str:
    """Normalize ``file_prefix`` into a safe filename component."""
    normalized_prefix = re.sub(PREFIX_SANITIZE_PATTERN, "-", file_prefix.strip())
    normalized_prefix = normalized_prefix.strip("-")
    if not normalized_prefix:
        raise ValueError("A non-empty file prefix is required")
    return normalized_prefix


def default_prefix() -> str:
    """Return a readable timestamp-based prefix for one generated file set."""
    return datetime.now().strftime(DEFAULT_PREFIX_FORMAT)


def wrap_base64(encoded_text: str) -> str:
    """Split ``encoded_text`` into PEM-width lines."""
    return "\n".join(
        encoded_text[index:index + PEM_LINE_LENGTH]
        for index in range(0, len(encoded_text), PEM_LINE_LENGTH)
    )


def build_pem_payload(file_prefix: str, file_role: str) -> str:
    """Create one PEM-style block for ``file_role`` within the ``file_prefix`` set."""
    generated_at = datetime.now().isoformat(timespec="seconds")
    payload_seed = "|".join(
        [
            "svr-credentials-mgr",
            file_prefix,
            file_role,
            generated_at,
            "test-material",
        ]
    ).encode(TEXT_ENCODING)
    payload_bytes = b"".join(
        hashlib.sha256(payload_seed + f":{digest_index}".encode(TEXT_ENCODING)).digest()
        for digest_index in range(8)
    )
    encoded_payload = base64.b64encode(payload_bytes).decode(TEXT_ENCODING)
    pem_label = ROLE_TO_PEM_LABEL[file_role]
    return (
        f"-----BEGIN {pem_label}-----\n"
        f"{wrap_base64(encoded_payload)}\n"
        f"-----END {pem_label}-----\n"
    )


def generate_test_certificate_files(
    output_directory: Path,
    file_prefix: str | None = None,
) -> dict[str, Path]:
    """Generate one complete set of test files and return their output paths."""
    selected_prefix = sanitize_prefix(file_prefix) if file_prefix else default_prefix()
    output_directory.mkdir(parents=True, exist_ok=True)
    generated_files: dict[str, Path] = {}
    for file_role, file_name in ROLE_TO_FILENAME.items():
        destination_path = output_directory / f"{selected_prefix}-{file_name}"
        destination_path.write_text(
            build_pem_payload(selected_prefix, file_role),
            encoding=TEXT_ENCODING,
        )
        generated_files[file_role] = destination_path
    return generated_files


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options for the test certificate generator."""
    argument_parser = argparse.ArgumentParser(
        description="Generate PEM-style test certificate and key files."
    )
    argument_parser.add_argument(
        "file_prefix",
        nargs="?",
        help="Optional file prefix. Defaults to a readable timestamp.",
    )
    argument_parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=f"Destination folder for generated files. Default: {DEFAULT_OUTPUT_DIRECTORY}",
    )
    return argument_parser.parse_args()


def main() -> None:
    """Generate one set of test certificate files and print the resulting paths."""
    arguments = parse_arguments()
    generated_files = generate_test_certificate_files(
        Path(arguments.output_dir).expanduser().resolve(),
        arguments.file_prefix,
    )
    for file_role, destination_path in generated_files.items():
        print(f"{file_role}: {destination_path}")


if __name__ == "__main__":
    main()
