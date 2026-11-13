<!--
Copyright 2026 opamp.info
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

# Dynamic Application Security Testing

The developer CLI runs OWASP ZAP 2.17.0, pinned by its multi-architecture OCI digest, in Docker or
Podman. By default, it sequentially builds and scans HTTP and HTTPS variants of a separate full
OpAMP server deployment containing the provider, Config Editor, Config Catalog, Client Config
Generator, and Server Credentials plugins.
The ZAP image contains the scanner; no host-side Java or ZAP installation is required.
The command is intentionally separate from `build secure`: static checks can start from source,
whereas DAST needs a reachable runtime and a full scan sends attack payloads.

## Prerequisites

- Install Docker Engine, Docker Desktop, or Podman.
- Use only a disposable deployment for a `full` scan.
- Keep the ZAP API and target service away from untrusted networks.

The CLI selects `OPAMP_CONTAINER_RUNTIME` first, then Docker, then Podman. Use `--runtime docker`
or `--runtime podman` to make the selection explicit.

## Scan The Isolated Full Application

Run a passive baseline from either PowerShell or a POSIX shell:

```bash
opamp-dev-cli build dast baseline
```

The command first builds and scans `opamp-dast-full-app:local` over HTTP. After that scan completes
successfully, it builds and scans `opamp-dast-full-app-https:local` over HTTPS. Each target uses the
locked server dependency set and installs only runtime dependencies. For each pass, the CLI creates
a unique private container network, starts the application without publishing a host port, waits
for its health check, runs ZAP on the same network, and then removes the application container and
network even when the scan fails. An HTTP failure stops the sequence before HTTPS starts.

ZAP uses `http://opamp-dast-target:8080` for the first pass and
`https://opamp-dast-target:8443` for the second. Host processes and host ports are not reachable
through this private alias, so an unrelated development server cannot become the scan target. The
runtime images do not contain source-checkout test tools, `node_modules`, coverage output,
`/docs`, or `/dev-notes`. The root `.dockerignore` also prevents those directories from entering
the build context.

The HTTPS image generates a short-lived, self-signed RSA test certificate during its Docker build.
Its subject alternative names cover `opamp-dast-target`, `localhost`, and `127.0.0.1`. The private
key exists only inside the disposable image and is not stored in the repository or build context.
The HTTPS provider configuration references `/app/tls/server.crt` and `/app/tls/server.key`.

The scan hook seeds the provider UI and the Config Editor, Config Catalog, Client Config
Generator, and Server Credentials pages before spidering. This ensures JavaScript-populated menu
entries do not prevent the traditional spider from inspecting installed plugin surfaces.

## Scan A Separately Managed Deployment

Use `--external-target` only when intentionally testing a deployment managed outside the DAST
command:

```bash
opamp-dev-cli build dast baseline \
  --external-target \
  --target http://host.docker.internal:8080 \
  --scope host-provider
```

For Docker, the CLI adds `host.docker.internal:host-gateway` when that host alias is selected,
allowing the same external-target command to work on Windows and Linux. Ensure the selected port
belongs to the application and never point DAST at a repository-root static file server.

For a provider started directly on the host, bind it to a container-reachable interface before
running the external scan:

```bash
python -m opamp_provider.server --host 0.0.0.0 --port 8080
```

Binding to `0.0.0.0` may expose the test service beyond the local machine. Retain an appropriate
host firewall and stop the service after testing.

## Scan A Compose Deployment

When ZAP joins an existing container network, use the target service name and network-specific
container options outside the CLI, or publish the service port to the host and use the default
host gateway. The current CLI deliberately does not guess or mutate an existing Compose network.
For the published-port approach:

```bash
opamp-dev-cli build dast baseline \
  --external-target \
  --target http://host.docker.internal:18083 \
  --scope st004
```

The `--scope` value controls report placement and accepts letters, numbers, dots, underscores,
and hyphens. It cannot contain a path separator.

## Rule Triage And Blocking Policy

Initial baseline scans do not fail on warning-only findings. Generate ZAP's complete default rule
file during a scan:

```bash
opamp-dev-cli build dast baseline --generate-rules
```

The generated policy is written to:

```text
dev-tools/runtime/security-reports/zap/provider/baseline/zap_generated_rules.conf
```

After reviewing every rule, copy it to a source-controlled file beneath `security/zap/`. On
PowerShell:

```powershell
Copy-Item `
  dev-tools/runtime/security-reports/zap/provider/baseline/zap_generated_rules.conf `
  security/zap/provider_rules.conf
```

On Linux or another POSIX shell:

```bash
cp dev-tools/runtime/security-reports/zap/provider/baseline/zap_generated_rules.conf \
  security/zap/provider_rules.conf
```

Use the reviewed file in subsequent scans:

```bash
opamp-dev-cli build dast baseline --rules-file security/zap/provider_rules.conf
```

The packaged ZAP format classifies rules as `FAIL`, `WARN`, `INFO`, or `IGNORE`. Prefer `FAIL`
for reviewed security requirements, retain `WARN` while a finding is being evaluated, and add an
explanation alongside every `IGNORE`. Add `--fail-on-warning` only after the warning baseline is
stable:

```bash
opamp-dev-cli build dast baseline \
  --rules-file security/zap/provider_rules.conf \
  --fail-on-warning
```

## Reviewed External Documentation Redirects

Every baseline and full scan loads the packaged `zap_scan_hooks.py` hook from its retained report
directory. The hook removes only `Big Redirect Detected` rule `10044` alerts whose ZAP
`Other Info` field identifies `https://htmlpreview.github.io` as the redirect destination. This
covers expected redirects from unknown local routes, including `/robots.txt` and `/sitemap.xml`,
to the externally rendered project documentation.

The local response is still requested and passively scanned. Rule `10044` remains enabled for
redirects to every other destination, and every other alert raised on the same local response is
retained. The hook deletes a matching reviewed alert from the live ZAP session before packaged
scan counts and HTML, JSON, XML, and Markdown reports are generated; it does not globally ignore
the redirect rule or exclude either local route from the spider.

## Active Full Scan

A full scan spiders the application and sends active attack payloads. It requires an explicit
acknowledgement so it cannot be selected accidentally:

```bash
opamp-dev-cli build dast full \
  --rules-file security/zap/provider_rules.conf \
  --allow-active-scan
```

Do not aim this command at a production service, shared development data, or a deployment whose
state cannot be discarded. Authentication and multi-user workflows should move to a reviewed ZAP
Automation Framework plan rather than placing bearer tokens in shell history.

## Verify Browser Security Response Headers

The provider and standalone browser services apply the following deny-by-default response
headers globally, including successful pages, redirects, authentication failures, and error
responses:

```text
Content-Security-Policy: frame-ancestors 'none'; form-action 'self'
Content-Security-Policy-Report-Only: default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-src 'none'; manifest-src 'self'; worker-src 'none'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
```

From PowerShell, inspect a running provider with:

```powershell
(Invoke-WebRequest -Uri http://localhost:8080/ui -UseBasicParsing).Headers |
  Format-List Content-Security-Policy, Content-Security-Policy-Report-Only, X-Frame-Options, X-Content-Type-Options
```

From Linux or another POSIX shell:

```bash
curl --silent --show-error --head http://localhost:8080/ui \
  | grep --extended-regexp --ignore-case \
      '^(content-security-policy|content-security-policy-report-only|x-frame-options|x-content-type-options):'
```

ZAP should no longer report `Missing Anti-clickjacking Header`, a missing `form-action` directive,
or an `X-Content-Type-Options` header that is absent or not set to `nosniff` for protected
responses. The strict report-only header intentionally does not suppress ZAP findings against the
less restrictive enforced policy. Packaged UI templates now load scripts and styles from
same-origin assets, avoid HTML event-handler and style attributes, and use system font stacks
instead of Google Fonts. Use browser console or reporting-endpoint violations to check runtime
DOM changes and deployment-specific overrides before enforcing the strict policy. Retain the
header and HTML compatibility assertions in component tests as the primary regression checks;
use DAST to verify the deployed target and any gateway in front of it.

## Reports And Exit Behavior

Each run replaces the stable files below:

```text
dev-tools/runtime/security-reports/zap/<scope>/<mode>/zap_report.html
dev-tools/runtime/security-reports/zap/<scope>/<mode>/zap_report.json
dev-tools/runtime/security-reports/zap/<scope>/<mode>/zap_report.xml
dev-tools/runtime/security-reports/zap/<scope>/<mode>/zap_report.md
```

Those paths contain the HTTP result. The sequential HTTPS pass writes the equivalent files without
overwriting HTTP evidence:

```text
dev-tools/runtime/security-reports/zap/<scope>/<mode>/https/zap_report.html
dev-tools/runtime/security-reports/zap/<scope>/<mode>/https/zap_report.json
dev-tools/runtime/security-reports/zap/<scope>/<mode>/https/zap_report.xml
dev-tools/runtime/security-reports/zap/<scope>/<mode>/https/zap_report.md
```

Image build failures, application health-check failures, unreachable targets, invalid
configuration, and findings classified as `FAIL` fail the command. Warning-only results are
non-blocking unless `--fail-on-warning` is set. Use `--spider-minutes` and
`--startup-timeout-minutes` to adjust the default two-minute spider and five-minute ZAP
startup/passive-scan wait.

The source for this workflow is `dev-tools/src/opamp_dev_tools/dast.py`, and its unit tests are in
`dev-tools/tests/test_dast.py`. The reviewed redirect filter is implemented in
`dev-tools/src/opamp_dev_tools/dast_scan_hooks.py`. The HTTP and HTTPS image targets are defined by
`dev-tools/docker/dast/Dockerfile`, using `dev-tools/docker/dast/opamp.json` and
`dev-tools/docker/dast/opamp-https.json` respectively. ZAP's upstream references are the
[Docker scan documentation](https://www.zaproxy.org/docs/docker/) and
[Automation Framework documentation](https://www.zaproxy.org/docs/automate/automation-framework/).
