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

# API Gateway Recommendations

This guide defines a recommended baseline for fronting the provider with an API gateway (for example Kong), and how to adjust OpAMP auth configuration when clients are remote or external to a controlled environment.

## Why this matters

The provider exposes multiple endpoint classes with different risk profiles:

- Operator endpoints: `/ui`, `/help`, `/doc-set`, `/api/*`
- MCP/tool endpoints: `/tool`, `/tool/*`, `/sse`, `/messages`, `/mcp`, `/mcp/*`
- Agent transport endpoint: `/v1/opamp` (HTTP + WebSocket)

If any of these are reachable directly from untrusted networks, a gateway policy should be treated as mandatory rather than optional.

## General Gateway Requirements (Recommended Baseline)

1. Single ingress path:
   - All external traffic must pass through the gateway.
   - Do not expose provider directly on public interfaces.
2. Origin isolation:
   - Bind provider to loopback or private network only.
   - Enforce firewall/security-group rules to block direct access.
3. TLS everywhere:
   - Terminate TLS at the gateway.
   - Use TLS between gateway and provider where possible.
4. Route-level authn/authz:
   - Apply per-route policies; do not share one permissive rule for all paths.
   - Separate operator access from agent/MCP access.
5. WebSocket/SSE support:
   - Ensure gateway auth policies are applied to WebSocket handshake routes and SSE routes, not only REST routes.
6. Request protection:
   - Add request size limits, rate limits, and connection limits per route.
   - Set conservative read/connect timeouts.
7. Header hygiene:
   - Strip or overwrite inbound identity/auth headers not explicitly trusted.
   - Forward only required headers to upstream.
8. Auditability:
   - Log auth decisions, route, source IP, and upstream status.
   - Alert on repeated 401/403 bursts and unusual request volume.

## Browser-Origin And Service-Origin Controls

No browser header or token proves that a request was created by the project UI. A user or
automation client with the same valid session and authorization can reproduce browser requests.
Use origin-related controls as layers rather than as a substitute for authentication and
authorization:

1. Session-authenticated browser routes should use session-bound CSRF protection for mutating
   requests.
2. Strict CORS allowlists and `Origin`/`Referer` checks are useful early filters, but those
   headers are not an identity boundary for non-browser clients.
3. High-risk mutations may add a short-lived nonce and timestamp to detect replay. Any signing
   material delivered to a browser must still be treated as extractable by the user controlling
   that browser.
4. Machine-to-machine routes should use a distinct authorization scope and, where appropriate,
   mTLS or another workload identity mechanism.
5. UI, automation, agent, and MCP routes should remain partitioned so rate limits, request-shape
   validation, audit policy, and incident response can differ by caller class.

## Environment Profiles and Config Amendments

## Profile A: Controlled/Internal Clients

Use this only when all clients run inside a tightly controlled network and direct exposure is blocked.

Recommended provider settings:

```json
{
  "provider": {
    "opamp-use-authorization": "config-token",
    "ui-use-authorization": "config-token"
  }
}
```

Notes:

- `jwt` is still preferred over `static` when an IdP is available.
- Set both static token environment variables:
  - `OPAMP_AUTH_STATIC_TOKEN` for `/v1/opamp`
  - `UI_AUTH_STATIC_TOKEN` for non-OpAMP routes (`/api`, `/tool`, `/sse`, `/messages`, `/mcp`, `/ui`, `/help`, `/doc-set`)

## Profile B: Remote/External or Mixed-Trust Clients

Use this when any client or operator is outside a controlled environment (internet, partner network, unmanaged edge, or unknown hosts).

Recommended provider settings:

```json
{
  "provider": {
    "opamp-use-authorization": "idp",
    "ui-use-authorization": "idp"
  }
}
```

Recommended environment variables:

```bash
# OpAMP transport (/v1/opamp)
export OPAMP_AUTH_JWT_ISSUER='https://issuer.example.com/realms/opamp'
export OPAMP_AUTH_JWT_AUDIENCE='opamp-mcp'
export OPAMP_AUTH_JWT_JWKS_URL='https://issuer.example.com/realms/opamp/protocol/openid-connect/certs'

# Non-OpAMP routes (/api, /tool, /sse, /messages, /mcp, /ui, /help, /doc-set)
export UI_AUTH_JWT_ISSUER='https://issuer.example.com/realms/opamp'
export UI_AUTH_JWT_AUDIENCE='opamp-ui'
export UI_AUTH_JWT_JWKS_URL='https://issuer.example.com/realms/opamp/protocol/openid-connect/certs'
```

Recommended gateway policy shape:

1. Operator routes (`/ui`, `/help`, `/doc-set`, `/api/*`):
   - OIDC login, MFA, and role/group checks.
2. MCP/tool routes (`/tool*`, `/mcp*`, `/sse`, `/messages`):
   - JWT validation with strict audience/issuer controls.
3. Agent transport (`/v1/opamp`):
   - JWT validation and/or mTLS client identity.
   - Apply request limits separately from UI/API traffic.

## Trust On First Use (TOFU) for `/v1/opamp`

TOFU can help bootstrap trust for `/v1/opamp`, then require bearer authentication on
subsequent requests. It is not a replacement for mTLS or strict gateway policy,
especially for external networks.

## Minimum Checklist Before External Exposure

1. Provider is not directly internet-accessible.
2. Gateway route auth is in place for `/api/*`, `/tool*`, `/mcp*`, `/sse`, `/messages`, and `/v1/opamp`.
3. JWT issuer/audience validation is configured.
4. WebSocket and SSE routes are covered by auth and rate limiting.
5. Request/body limits are enforced for `/v1/opamp` and `/api/*`.
6. Logging and alerting are enabled for auth failures and high request rates.
