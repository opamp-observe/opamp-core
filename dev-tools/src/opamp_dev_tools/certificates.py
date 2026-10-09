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

"""Certificate generation and Keycloak setup helpers."""

from __future__ import annotations

import datetime as dt
import ipaddress
import json
import os
import pathlib
from collections.abc import Iterable

from .runtime import CommandRuntime, prompt_bool, prompt_int, prompt_text

DEFAULT_CERT_FILE = "certs/provider-server.pem"
DEFAULT_KEY_FILE = "certs/provider-server-key.pem"
DEFAULT_COMMON_NAME = "localhost"
DEFAULT_VALIDITY_DAYS = 365
DEFAULT_DNS_NAMES = ("localhost",)
DEFAULT_IP_ADDRESSES = ("127.0.0.1",)
DEFAULT_TRUST_ANCHOR_MODE = "none"
TRUST_ANCHOR_MODES = ("none", "partial_chain", "full_chain_to_root")


def generate_self_signed_certificate(
    runtime: CommandRuntime,
    *,
    python_exe: str,
    cert_file: str | None = None,
    key_file: str | None = None,
    common_name: str | None = None,
    validity_days: int | None = None,
    dns_names: list[str] | None = None,
    ip_addresses: list[str] | None = None,
    force: bool = False,
    skip_dependency_install: bool = False,
) -> bool:
    """Generate a self-signed local development certificate."""
    if not skip_dependency_install:
        runtime.ensure_python_module(
            python_exe=python_exe,
            module_name="cryptography",
            pip_package="cryptography",
        )

    interactive_mode = all(
        value is None
        for value in (cert_file, key_file, common_name, validity_days, dns_names, ip_addresses)
    ) and not force

    if interactive_mode:
        cert_file = prompt_text("Certificate output path", default=DEFAULT_CERT_FILE)
        key_file = prompt_text("Private key output path", default=DEFAULT_KEY_FILE)
        common_name = prompt_text("Certificate common name", default=DEFAULT_COMMON_NAME)
        validity_days = prompt_int("Validity in days", default=DEFAULT_VALIDITY_DAYS)
        dns_names = _split_csv(prompt_text("DNS SAN values", default=",".join(DEFAULT_DNS_NAMES)))
        ip_addresses = _split_csv(prompt_text("IP SAN values", default=",".join(DEFAULT_IP_ADDRESSES)))
        force = prompt_bool("Overwrite existing output files", default=False)
    else:
        cert_file = cert_file or DEFAULT_CERT_FILE
        key_file = key_file or DEFAULT_KEY_FILE
        common_name = common_name or DEFAULT_COMMON_NAME
        validity_days = validity_days if validity_days is not None else DEFAULT_VALIDITY_DAYS
        dns_names = dns_names or list(DEFAULT_DNS_NAMES)
        ip_addresses = ip_addresses or list(DEFAULT_IP_ADDRESSES)

    cert_path = _prepare_output_path(runtime.repo_root / cert_file, force=force)
    key_path = _prepare_output_path(runtime.repo_root / key_file, force=force)
    _write_certificate(
        cert_path=cert_path,
        key_path=key_path,
        common_name=common_name,
        validity_days=validity_days,
        dns_names=dns_names,
        ip_addresses=ip_addresses,
    )
    runtime.info("[OK] Self-signed certificate created")
    runtime.info(f"      cert: {cert_path}")
    runtime.info(f"      key : {key_path}")
    runtime.info("[INFO] See docs/self_signed_tls_setup.md for configuration updates.")
    return False


def configure_keycloak(runtime: CommandRuntime) -> bool:
    """Guide the user through local Keycloak auth configuration."""
    runtime_value = prompt_text("Container runtime (docker/podman)", default="docker")
    env = os.environ.copy()
    env["CONTAINER_RUNTIME"] = runtime_value
    env["KEYCLOAK_HOST_PORT"] = prompt_text("Keycloak host port", default="8081")
    env["KEYCLOAK_REALM"] = prompt_text("Realm name", default="opamp")
    env["KEYCLOAK_CLIENT_ID"] = prompt_text("Client ID", default="opamp-mcp")
    env["KEYCLOAK_CLIENT_SECRET"] = prompt_text("Client secret", default="opamp-mcp-secret")
    env["KEYCLOAK_USER"] = prompt_text("Test user", default="opamp-user")
    env["KEYCLOAK_USER_PASSWORD"] = prompt_text("Test user password", default="opamp-password")
    runtime.run(
        [str(runtime.repo_root / "scripts" / "configure_keycloak.sh")],
        cwd=runtime.repo_root,
        env=env,
    )
    return False


def ensure_provider_tls_config(
    runtime: CommandRuntime,
    *,
    config_file: str | None = None,
    cert_file: str | None = None,
    key_file: str | None = None,
    trust_anchor_mode: str | None = None,
) -> bool:
    """Ensure provider.tls settings exist in one OpAMP config JSON file."""
    interactive_mode = any(
        value is None for value in (config_file, cert_file, key_file, trust_anchor_mode)
    )
    if interactive_mode:
        config_file = prompt_text("Config JSON path", default="config/opamp.json")
        cert_file = prompt_text("TLS certificate path", default=DEFAULT_CERT_FILE)
        key_file = prompt_text("TLS private key path", default=DEFAULT_KEY_FILE)
        trust_anchor_mode = prompt_text(
            "Trust anchor mode",
            default=DEFAULT_TRUST_ANCHOR_MODE,
        )

    if None in (config_file, cert_file, key_file, trust_anchor_mode):
        raise RuntimeError("Provider TLS configuration values were not resolved")

    normalized_trust_anchor_mode = str(trust_anchor_mode).strip()
    if normalized_trust_anchor_mode not in TRUST_ANCHOR_MODES:
        valid_modes = ", ".join(TRUST_ANCHOR_MODES)
        raise ValueError(
            f"invalid trust anchor mode `{trust_anchor_mode}`; valid values: {valid_modes}"
        )

    config_path = _resolve_repo_relative_path(runtime.repo_root, config_file)
    cert_path = _resolve_config_reference_path(runtime.repo_root, cert_file)
    key_path = _resolve_config_reference_path(runtime.repo_root, key_file)
    payload = _load_json_object(config_path)
    provider = payload.get("provider")
    if not isinstance(provider, dict):
        provider = {}
    tls = provider.get("tls")
    if not isinstance(tls, dict):
        tls = {}

    tls["cert_file"] = str(cert_path)
    tls["key_file"] = str(key_path)
    tls["trust_anchor_mode"] = normalized_trust_anchor_mode
    provider["tls"] = tls
    payload["provider"] = provider

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    runtime.info(f"[OK] Updated provider TLS config in {config_path}")
    runtime.info(f"      cert_file: {cert_path}")
    runtime.info(f"      key_file : {key_path}")
    runtime.info(f"      trust    : {normalized_trust_anchor_mode}")
    return False


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _prepare_output_path(path: pathlib.Path, *, force: bool) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}. Use force to overwrite.")
    return path


def _resolve_repo_relative_path(repo_root: pathlib.Path, raw_path: str) -> pathlib.Path:
    path = pathlib.Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def _resolve_config_reference_path(repo_root: pathlib.Path, raw_path: str) -> str:
    """Resolve local paths while preserving absolute POSIX deployment paths.

    Parameters
    ----------
    repo_root:
        Repository root used to resolve relative certificate references.
    raw_path:
        Certificate or key path stored in provider configuration.

    """
    expanded_path = pathlib.Path(raw_path).expanduser()
    if pathlib.PurePosixPath(raw_path).is_absolute() and not expanded_path.is_absolute():
        return raw_path
    return str(_resolve_repo_relative_path(repo_root, raw_path))


def _load_json_object(path: pathlib.Path) -> dict[str, object]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"Config root must be a JSON object: {path}")
    return payload


def _write_certificate(
    *,
    cert_path: pathlib.Path,
    key_path: pathlib.Path,
    common_name: str,
    validity_days: int,
    dns_names: list[str],
    ip_addresses: list[str],
) -> None:
    if validity_days <= 0:
        raise ValueError("validity period must be a positive integer")

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    san_entries: list[x509.GeneralName] = []
    for dns_name in _dedupe(dns_names):
        san_entries.append(x509.DNSName(dns_name))
    for ip_text in _dedupe(ip_addresses):
        san_entries.append(x509.IPAddress(ipaddress.ip_address(ip_text)))
    if not san_entries:
        raise ValueError("at least one SAN entry is required")

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "GB"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "OpAMP Local Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )
    utc_now = dt.datetime.now(dt.timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(utc_now - dt.timedelta(minutes=5))
        .not_valid_after(utc_now + dt.timedelta(days=validity_days))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(private_key=private_key, algorithm=hashes.SHA256())
    )
    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(certificate.public_bytes(encoding=serialization.Encoding.PEM))
    if os.name != "nt":
        os.chmod(key_path, 0o600)
