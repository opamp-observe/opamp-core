<!--
Copyright 2026 mp3monster.org
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Self-Signed TLS Certificate Setup

This guide shows how to use the developer CLI certificate helper to:

1. install required Python dependency (`cryptography`), and
2. generate a self-signed TLS certificate and private key for local provider HTTPS testing.

## CLI Location

- Command: `python dev-tools/main.py certificate generate`
- Help: `python dev-tools/main.py certificate generate --help`

The command `--help` output points to this document.

## What The Script Generates

By default, the script writes:

- certificate: `certs/provider-server.pem`
- private key: `certs/provider-server-key.pem`

Default SAN values:

- DNS: `localhost`
- IP: `127.0.0.1`

## Usage

Linux/macOS:

```bash
python3 dev-tools/main.py certificate generate
```

Windows (cmd or PowerShell):

```powershell
python dev-tools/main.py certificate generate
```

## Common Options

```bash
python3 dev-tools/main.py certificate generate \
  --cert-file certs/provider-server.pem \
  --key-file certs/provider-server-key.pem \
  --common-name localhost \
  --dns-name localhost \
  --dns-name provider.local \
  --ip-address 127.0.0.1 \
  --days 365 \
  --force
```

If dependency auto-install is not desired:

```bash
python3 dev-tools/main.py certificate generate --skip-dependency-install
```

## Configuration Updates Required

Apply the following values where relevant.

## 1) Provider Config (`config/opamp.json`)

Add/update `provider.tls`:

```json
{
  "provider": {
    "tls": {
      "enabled": true,
      "cert_file": "certs/provider-server.pem",
      "key_file": "certs/provider-server-key.pem",
      "trust_anchor_mode": "none"
    }
  }
}
```

Behavior notes:

- If the `provider.tls` section is missing, provider runs HTTP-only.
- If `provider.tls` is present and `enabled` is omitted, TLS defaults to enabled.
- Set `provider.tls.enabled` to `false` to keep the section but force HTTP-only mode.

If you start provider with `scripts/run_opamp_server.sh --https` or
`scripts\\run_opamp_server.cmd --https`, the TLS cert/key/trust values are generated/updated automatically.
`provider.tls.enabled` can be set explicitly, but defaults to enabled when omitted.

Also ensure the consumer URL in the same file uses HTTPS:

```json
{
  "consumer": {
    "server_url": "https://localhost:8080"
  }
}
```

You can also apply the `provider.tls` block with the developer CLI:

```bash
python3 dev-tools/main.py certificate ensure-provider-config \
  --config-file config/opamp.json \
  --cert-file certs/provider-server.pem \
  --key-file certs/provider-server-key.pem \
  --trust-anchor-mode none
```

## 2) Fluentd Consumer Config (`consumer/opamp-fluentd.json`)

Set:

```json
{
  "consumer": {
    "server_url": "https://localhost:8080"
  }
}
```

## Self-Signed Certificate Impact: CA Validation

A self-signed server certificate is not chained to a public CA. If the consumer is doing strict CA validation, HTTPS validation will fail unless you disable verification or trust that cert/CA explicitly.

For the TLS model documented in `docs/tls_https_mtls_revision.md`, the impacted client setting is:

```json
{
  "consumer": {
    "tls": {
      "verify_server": false
    }
  }
}
```

Use `verify_server=false` for local development only.

## Recommended Development-Only Pattern

1. Generate the self-signed certificate/key with the developer CLI.
2. Enable provider TLS using the generated files.
3. Point consumer `server_url` to `https://...`.
4. Disable client CA verification for local self-signed usage (`consumer.tls.verify_server=false`).

## Troubleshooting

- `Missing dependency: cryptography`
  - Re-run without `--skip-dependency-install`, or install manually:
    - `python -m pip install --upgrade cryptography`
- Certificate hostname mismatch
  - Ensure the host in `server_url` is included in SAN entries (`--dns-name`, `--ip-address`).
- Existing output files
  - Use `--force` to overwrite existing cert/key files.

## Container Verification

The [`ST-004B TLS profile`](../tests/test-containers/st004b/readme.md) generates
an isolated self-signed certificate and verifies all of the following:

- plain HTTP cannot communicate with the HTTPS listener;
- default system trust rejects the self-signed certificate;
- an explicit CA file permits API access and consumer registration;
- a consumer without the CA remains unregistered and logs the certificate
  verification failure.

Run it with:

```bash
tests/test-containers/st004b/scripts/run_st004b.sh tls
```
