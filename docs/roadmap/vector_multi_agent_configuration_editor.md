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

# Multi-Agent Configuration Editor and Vector Support

Status: proposed roadmap specification  
Research baseline: 4 October 2026

## Purpose

This document specifies how the existing `config-service` editor can become a
multi-agent configuration editor and add Vector as the first new format after
Fluent Bit and Fluentd. It is intended to be detailed enough to drive
specification-led implementation in the OpAMP server without requiring the
implementer to infer the architecture from the current Fluent Bit code.

The recommended approach is to reuse the editor's version registry, field
rendering, YAML handling, validation workflow, and OpAMP integration, but not
the Fluent Bit document shape. Vector configuration is a named topology graph;
representing it as Fluent Bit-style plugin arrays would discard component
identity and connection semantics.

## Decision Summary

1. Add a server-side configuration-format adapter registry. Parsing, rendering,
   validation, file metadata, and editor capabilities must be selected through
   an adapter rather than `if fluentbit` and `if fluentd` branches.
2. Keep each agent's native configuration tree as the canonical in-memory
   `config` value. Do not invent one universal pipeline model that cannot round
   trip agent-specific fields.
3. Generate a versioned Vector editor manifest from the JSON Schema emitted by
   the matching Vector binary with `vector generate-schema`.
4. Use JSON Schema for immediate structural validation and `vector validate`
   for authoritative semantic, topology, VRL, and component validation.
5. Add generic named-map and connection editors to the browser UI. These are
   required for Vector's `sources`, `transforms`, and `sinks` maps.
6. Retain the current Fluent Bit and Fluentd endpoints as compatibility shims
   while moving the browser to generic document endpoints.
7. Deliver Vector support incrementally: lossless load/save and form editing
   first, topology-aware connections second, and a visual graph only if it
   proves useful. A graph canvas is not required for the initial release.

## Vector Research

### Configuration model

Vector recommends YAML while also accepting TOML and JSON. A full configuration
contains top-level global options and named component maps. The principal
pipeline sections are:

| Section | Shape | Role |
| --- | --- | --- |
| `sources` | Map from component ID to component object | Receives observability events. |
| `transforms` | Map from component ID to component object | Changes, filters, samples, or routes events. |
| `sinks` | Map from component ID to component object | Sends events to a destination. |
| `enrichment_tables` | Named map | Supplies reference data to transforms. |
| `tests` | Array of named test objects | Exercises transforms against test events. |
| Global sections | Objects or scalar values | Configure API, schema, secrets, data directory, health, and other process behavior. |

Every component object has a `type` discriminator. Transforms and sinks use
`inputs` to refer to upstream component IDs or wildcard expressions. This is a
directed topology, not merely three independent lists. Renaming or deleting a
component therefore requires reference checks and an explicit repair strategy.

Vector can load several configuration files and can also use automatic
namespacing with directories such as `sources/`, `transforms/`, and `sinks/`.
The initial implementation should edit one complete YAML document. The backend
contract must nevertheless allow a future document-set adapter; Vector's merge
behavior must not be implemented through Fluent Bit's include semantics.

Sources:

- [Vector configuration overview](https://vector.dev/docs/reference/configuration/)
- [Vector pipeline components reference](https://vector.dev/docs/reference/configuration/pipeline-components/)
- [Vector configuration unit tests](https://vector.dev/docs/reference/configuration/unit-tests/)
- [Vector components index](https://vector.dev/components/)

### Authoritative configuration schema

Vector has an experimental `generate-schema` command:

```text
vector generate-schema -o vector-<version>-schema.json
```

The output is a JSON Schema for the complete configuration supported by that
specific Vector binary. It contains component unions for sources, transforms,
and sinks, field descriptions, defaults, enums, deprecation markers, references,
and Vector-specific `_metadata`. Vector's configuration-schema RFC describes
the schema as the code-derived source of truth for external validation and
interactive editing. The current generator identifies its schema dialect as
JSON Schema 2019-09.

The generated schema is suitable as an upstream artifact, but not as the UI's
direct rendering contract. It uses `$ref`, `allOf`, `oneOf`, nullable unions,
discriminators, and metadata that a browser form renderer would otherwise have
to reinterpret on every page load. A deterministic build tool should compile it
into the smaller editor manifest defined below.

The schema is tied to the producing binary. A schema generated by one Vector
version must not be labelled as another version, and the editor must not assume
that the latest schema validates older agents.

Sources:

- [Vector configuration schema RFC](https://github.com/vectordotdev/vector/blob/master/rfcs/2022-02-23-9481-config-schema.md)
- [Vector schema autocompletion guide](https://vector.dev/guides/developer/config-autocompletion/)
- [Vector schema generator implementation](https://rust-doc.vector.dev/src/vector_config_common/schema/generator.rs.html)

### Authoritative validation

Vector provides a native validation command. For an editor-produced YAML file,
the baseline dry run is:

```text
vector validate --no-environment --config-yaml <configuration-path>
```

`--no-environment` avoids network, component, and sink health checks during an
editor validation. Environment-variable interpolation remains disabled unless
an administrator explicitly opts into Vector's dangerous interpolation flag.
The server must not enable it automatically because validation output or a
rendered preview could expose secrets.

JSON Schema catches document shape and field constraints quickly. Native
validation remains necessary for topology, VRL compilation, semantic checks,
and rules evaluated only while Vector builds components.

Source: [Vector CLI reference](https://vector.dev/docs/reference/cli/)

## Open-Source Editor Research

[VortexFlow](https://github.com/VortexFLOW-dev/VortexFLOW) is an open-source,
self-hosted Vector control plane under MPL-2.0. Its published feature set
includes a visual topology editor, schema-generated source and sink forms, VRL
editing, native Vector YAML output, `vector validate`, fleet rollout, and live
event taps. Its implementation runs `vector generate-schema`, caches the result,
and falls back to a bundled schema-derived catalog when the binary is absent.

VortexFlow demonstrates that schema-driven Vector forms are practical, but it
should be treated as a design reference rather than embedded into this project:

- its React/TypeScript/React Flow frontend conflicts with this repository's
  modular vanilla JavaScript UI direction;
- its fleet database, deployment agents, monitoring, and RBAC are outside the
  configuration editor's initial scope;
- its current generated catalog intentionally flattens only part of the schema,
  limits object traversal depth, and focuses on sources and sinks, so it is not
  a lossless general Vector editor; and
- source reuse would require an explicit MPL-2.0 compatibility and attribution
  review. This specification does not require copying VortexFlow code.

Useful primary references:

- [VortexFlow project and feature description](https://github.com/VortexFLOW-dev/VortexFLOW)
- [Schema-to-catalog converter](https://github.com/VortexFLOW-dev/VortexFLOW/blob/main/frontend/src/lib/catalogGen.ts)
- [Server-side schema provider](https://github.com/VortexFLOW-dev/VortexFLOW/blob/main/backend/app/services/catalog_schema.py)
- [Schema-driven component form](https://github.com/VortexFLOW-dev/VortexFLOW/blob/main/frontend/src/components/catalog/ComponentConfigForm.tsx)

A hosted Vector configuration generator also exists, but no authoritative
open-source repository or software licence was identified during this research.
It should not be classified as an open-source implementation or used as a code
dependency without further evidence.

## Current Config-Service Assessment

The existing implementation already contains several foundations for a
multi-agent editor:

- `catalog-registry.json`, `service-registry.json`, and
  `parser-registry.json` resolve definitions by configuration type and version;
- `/versions`, `/catalog/<version>`, `/schema/<version>`, `/validate/<version>`,
  and `/render/yaml/<version>` accept a `config_type` query parameter;
- the field renderer handles required and optional values, enums, booleans,
  arrays, nested metadata, descriptions, defaults, and documentation links;
- the external validation registry resolves commands by agent type and version;
- `config-service` can run standalone or as an OpAMP server component; and
- the consumer already has a Vector implementation that can receive remote
  configuration and report effective configuration.

The principal blockers are format assumptions spread across otherwise generic
layers:

| Area | Current assumption | Required change |
| --- | --- | --- |
| Browser document state | `service`, `env`, `parsers`, `upstream_servers`, and `pipeline.inputs/filters/outputs` always exist. | Let a format adapter supply an empty document and section descriptors. |
| Browser layout | Panels and visibility checks are Fluent Bit or Fluentd specific. | Render panels from editor capabilities and collection descriptors. |
| Component renderer | Plugins are arrays whose identity comes from `name`. | Add named-map collections with a separate component ID and `type` discriminator. |
| Catalog validation | Catalogs must expose `inputs`, `filters`, and `outputs`. | Validate a generic editor-manifest contract; keep legacy catalog translation for existing agents. |
| Schema compilation | `SchemaService` branches between Fluent Bit and Fluentd. | Add schema-provider adapters; pass through Vector's upstream schema. |
| Semantic validation | `ValidationService` contains engine-specific branches. | Split structural, common graph, rules-engine, and adapter validation stages. |
| Parse/render API | Parse routes are format-named and render selection is hard-coded. | Add generic document routes that dispatch through the adapter registry. |
| Include handling | Non-Fluentd content is treated as Fluent Bit YAML. | Make document composition an adapter capability. |
| File handling | YAML implies Fluent Bit and `.conf` implies Fluentd. | Resolve format from explicit metadata first, then registered extensions and content hints. |
| Native dry run | The registry is generic, but suffixes and adapters know only Fluent Bit/Fluentd. | Add a dedicated Vector adapter and `.yaml` file metadata. |

### Affected code map

Implementation should begin with these ownership boundaries:

| Current file | Responsibility in the refactor |
| --- | --- |
| [`app.py`](../../config-service/src/config_service/app.py) | Construct and register format adapters, schema providers, and validators. |
| [`routes/api.py`](../../config-service/src/config_service/routes/api.py) | Replace format branches with generic document dispatch and retain compatibility routes. |
| [`models/contracts.py`](../../config-service/src/config_service/models/contracts.py) | Add the common document envelope, capability, render, and validation request/response models. |
| [`catalog_service.py`](../../config-service/src/config_service/services/catalog_service.py) | Load generic editor manifests instead of enforcing only three Fluent-style plugin groups. |
| [`schema_service.py`](../../config-service/src/config_service/services/schema_service.py) | Delegate schema acquisition/compilation by format; preserve current compilers behind legacy adapters. |
| [`validation_service.py`](../../config-service/src/config_service/services/validation_service.py) | Orchestrate common validation stages and move engine semantics into adapters. |
| [`include_document_service.py`](../../config-service/src/config_service/services/include_document_service.py) | Delegate composition and include behavior rather than defaulting all YAML to Fluent Bit. |
| [`agent_validation/service.py`](../../config-service/src/config_service/agent_validation/service.py) | Add safe argv execution, timeout/output controls, and a Vector validation adapter. |
| [`config_ui.js`](../../config-service/src/config_service/html/config_ui.js) | Reduce to bootstrap/orchestration and remove the fixed Fluent document skeleton. |
| [`config_ui_api.js`](../../config-service/src/config_service/html/config_ui_api.js) | Call the generic formats and documents API. |
| [`config_ui_sections.js`](../../config-service/src/config_service/html/config_ui_sections.js) | Convert fixed sections into capability-registered section renderers. |
| [`config_ui_plugins.js`](../../config-service/src/config_service/html/config_ui_plugins.js) | Retain Fluent plugin extensions while moving common field/card behavior into generic modules. |

The existing tests under [`config-service/tests`](../../config-service/tests/),
[`config-service/ui-unit-tests`](../../config-service/ui-unit-tests/), and
[`config-service/ui-tests`](../../config-service/ui-tests/) are the migration
safety net and should be extended in the phase that changes each boundary.

## Reuse of the Fluent Bit Approach

The Fluent Bit approach is applicable at the framework level, not at the data
model level.

| Fluent Bit mechanism | Vector applicability | Decision |
| --- | --- | --- |
| Versioned generated catalogs | Strong | Reuse the registry pattern, deriving artifacts from `vector generate-schema`. |
| Schema-driven fields | Strong | Reuse field controls after adding nested objects, maps, unions, and code fields. |
| YAML parse/render | Strong | Reuse the YAML service while preserving native Vector maps and unknown keys. |
| External binary validation | Strong | Add `VectorValidationAdapter` using `vector validate`. |
| Input/filter/output plugin arrays | Weak | Do not reuse as the canonical Vector model. |
| Plugin `name` as type | Incompatible | Vector uses map key as component ID and `type` as implementation. |
| Fluent Bit filters | Incomplete mapping | Vector transforms are graph nodes with their own IDs and `inputs`. |
| Fluent Bit includes | Incompatible semantics | Add future Vector document-set composition separately. |
| Processor and route panels | Agent-specific | Keep behind Fluent Bit capabilities; do not expose for Vector. |

## Target Architecture

### Native document envelope

The browser and API should exchange a stable envelope while leaving `config`
native to the selected agent:

```json
{
  "config_type": "vector",
  "agent_version": "0.58.0",
  "serialization": "yaml",
  "config": {
    "sources": {},
    "transforms": {},
    "sinks": {}
  },
  "annotations": {},
  "included_documents": []
}
```

`included_documents` remains in the common envelope for compatibility. The
Vector adapter must reject or ignore it with a clear capability response until
Vector document-set support is implemented. Agent-specific values must never be
moved into the envelope merely to make the UI simpler.

### Configuration-format adapter

Add `config_service.formats` with a registry and a protocol similar to:

```python
class ConfigurationFormatAdapter(Protocol):
    """Provide one agent format's document lifecycle to config-service."""

    config_type: str

    def capabilities(self, version: str) -> FormatCapabilities: ...
    def empty_config(self, version: str) -> dict[str, Any]: ...
    def parse(self, text: str, version: str, source_path: Path | None) -> ParsedDocument: ...
    def render(self, document: ConfigDocument) -> RenderedDocument: ...
    def validate(self, document: ConfigDocument) -> list[ValidationIssue]: ...
    def editor_manifest(self, version: str) -> dict[str, Any]: ...
    def file_metadata(self) -> FileMetadata: ...
```

The concrete adapters should be `FluentBitFormatAdapter`,
`FluentdFormatAdapter`, and `VectorFormatAdapter`. Existing services may be
injected into the first two adapters during migration; they need not be
rewritten in the first change.

`FormatCapabilities` should explicitly describe:

- supported serializations and file extensions;
- root section kinds;
- comment and annotation support;
- include or document-set support;
- JSON Schema availability;
- native dry-run availability;
- named-component and topology support; and
- optional specialist editors such as Fluent Bit parsers or Vector VRL.

The application factory should register adapters once and expose only the
registry through routes. Routes must not import concrete adapter classes.

### Editor manifest

Create one generated editor manifest per agent version. It is a UI contract,
not a replacement for the authoritative JSON Schema. A Vector manifest should
contain:

```json
{
  "manifest_version": "1.0.0",
  "config_type": "vector",
  "agent_version": "0.58.0",
  "source_schema_dialect": "https://json-schema.org/draft/2019-09/schema",
  "source_schema_sha256": "<digest>",
  "sections": [
    {
      "key": "sources",
      "label": "Sources",
      "collection_kind": "named_map",
      "discriminator": "type",
      "connection_field": null
    },
    {
      "key": "transforms",
      "label": "Transforms",
      "collection_kind": "named_map",
      "discriminator": "type",
      "connection_field": "inputs"
    },
    {
      "key": "sinks",
      "label": "Sinks",
      "collection_kind": "named_map",
      "discriminator": "type",
      "connection_field": "inputs"
    }
  ]
}
```

Component variants should retain a JSON Schema reference or resolved subschema,
title, description, required fields, defaults, examples, deprecation state,
stability metadata, supported event types where available, and an upstream
documentation URL when one can be derived authoritatively.

The manifest compiler must support `$ref`, sibling constraints, `allOf`,
`oneOf`, `anyOf`, nullable values, arrays, maps, nested objects, constants,
enums, defaults, examples, formats, numeric/string bounds, and deprecations.
Unsupported constructs must be recorded as diagnostics and rendered through a
raw structured-value control. Silently dropping fields is unacceptable.

### Schema acquisition and provenance

Add a development tool such as
`config-service/dev-tools/generate_vector_assets.py`. For every supported
version it must:

1. execute an explicitly configured Vector binary with `--version`;
2. reject a binary whose reported version does not match the requested version;
3. execute `generate-schema` without a shell and with a timeout;
4. validate the returned JSON and its schema dialect;
5. write the immutable upstream schema beneath
   `json-schemas/vector/<version>/config-schema.json`;
6. compile the editor manifest beneath
   `json-definitions/vector/<version>/editor-manifest.json`;
7. write deterministic provenance containing the Vector version and source
   schema SHA-256 digest; and
8. support `--check` mode so CI fails when committed generated assets drift.

Generation must be an explicit maintainer action. The production server should
not download schemas from the internet. An optional locally configured Vector
binary may supply a live schema only when its version and digest are verified;
bundled artifacts remain the deterministic fallback.

### Generic API

Add these routes under the existing API version:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/formats` | List formats, versions, defaults, serializations, and capabilities. |
| `GET` | `/formats/<config_type>/<version>/editor-manifest` | Return the generated editor contract. |
| `GET` | `/formats/<config_type>/<version>/schema` | Return the authoritative document schema. |
| `POST` | `/documents/<config_type>/<version>/parse` | Parse text into the native document envelope. |
| `POST` | `/documents/<config_type>/<version>/render` | Render a native document with the requested serialization. |
| `POST` | `/documents/<config_type>/<version>/validate` | Run schema, semantic, rule, and optional native validation stages. |

Responses should use one validation issue model with `code`, `message`,
`severity`, `source`, `path`, and optional line/column. Validation sources should
include `json_schema`, `config_service`, and `vector`. Native output must be
parsed where stable and retained as a bounded diagnostic when it cannot be
mapped precisely.

The current routes remain operational and delegate to adapters:

- `/parse/fluentbit/<version>`;
- `/parse/fluentd/<version>`;
- `/render/yaml/<version>`;
- `/render/fluentd/<version>`;
- `/schema/<version>`; and
- `/validate/<version>`.

No compatibility route should contain new agent-specific behavior after the
adapter migration.

### Validation pipeline

Validation should run these stages in order:

1. Envelope and requested format/version validation.
2. JSON Schema validation using the dialect declared by the stored schema.
3. Common named-topology checks: valid IDs, duplicate IDs, missing input
   references, self-references, and cycles where Vector forbids them.
4. Agent adapter semantic checks.
5. Existing configurable rules-engine checks that declare compatibility with
   the selected format.
6. Optional native dry run through the matching Vector binary.

Use a dedicated `VectorValidationAdapter` even though the generic command
adapter can launch a process. It should build an argument array, invoke without
`shell=True`, apply a timeout, cap captured output, delete temporary files, and
redact environment values and secret-like configuration fields from logs. The
result must identify the requested and actual Vector versions.

### Browser refactor

Continue the existing `window.<ModuleName>.create(deps)` modular pattern. Split
format-independent state and behavior from specialist panels:

- `config_ui_state.js`: document envelope, selected format/version, dirty state,
  and persistence;
- `config_ui_format_registry.js`: capabilities and manifest lookup;
- `config_ui_document.js`: new/load/parse/render/validate orchestration;
- `config_ui_fields.js`: schema-driven scalar, object, array, map, union, and
  code controls;
- `config_ui_collections.js`: list and named-map collections;
- `config_ui_topology.js`: component IDs, `inputs`, reference integrity, rename,
  and deletion impact; and
- existing Fluent Bit parser, route, processor, and Fluentd nested-section
  modules registered as format-specific extensions.

The first Vector UI should provide:

- add, rename, clone, reorder for display, and delete for named components;
- source, transform, and sink type selection from the manifest;
- schema-driven component fields with required/optional state and help links;
- upstream `inputs` selection for transforms and sinks;
- clear impact reporting before a referenced component is renamed or removed;
- a VRL-aware multiline editor for code fields, with plain textarea fallback;
- global-options editing generated from the top-level schema;
- raw YAML preview and a raw structured-value escape hatch for unsupported
  schema constructs; and
- preservation of unknown keys and values during load/edit/save.

The initial topology view may be an ordered component list with connection
selectors. A later visual DAG must be a projection of the same native document,
not a second source of truth.

### Round-trip rule

Lossless round-trip behavior is a release requirement. Parsing a valid Vector
configuration, changing one supported field, and rendering it must preserve all
unmodified supported and unsupported values. Exact whitespace and comment
placement are not guaranteed by the existing YAML service, but a warning must
be shown before structured editing when comments cannot be preserved.

Unknown component types should appear as raw-editable components rather than
causing the complete document to fail to load. They may block schema validation
while still allowing the user to inspect and export the document.

## OpAMP Server Integration

The work remains inside the existing `config-service` component registered with
the provider. Vector does not require a new top-level server component.

Saved configuration metadata must carry `config_type`, `agent_version`, and
`serialization`. The server configuration catalog should use these values to
filter or warn when an operator assigns a configuration to an incompatible
client implementation. A Vector configuration is delivered as native YAML
through the existing OpAMP remote-configuration path; the Vector consumer then
reports the effective configuration using its current capability support.

Assignment and rollout must not depend on the editor manifest. The manifest is
editor metadata, while the rendered Vector document is the deployable artifact.
Before an offered configuration becomes eligible for assignment, server policy
may require successful validation against both the stored schema and the
configured matching Vector binary.

## Delivery Plan

### Phase 0: Characterization

- Add contract tests around current Fluent Bit and Fluentd versions, parse,
  render, validation, file load/save, and browser workflows.
- Capture representative fixtures containing comments, includes, nested fields,
  custom plugins, and unknown values.
- Record current endpoint responses so adapter migration can prove compatibility.

Exit criterion: no production behavior changes, and existing formats have a
repeatable compatibility baseline.

### Phase 1: Adapter seam

- Add document models, format capabilities, adapter protocol, and registry.
- Wrap current Fluent Bit and Fluentd services in adapters.
- Add generic routes and redirect browser calls to them.
- Retain and test all compatibility routes.

Exit criterion: Fluent Bit and Fluentd pass existing backend, UI unit, and
Playwright tests through the adapter registry.

### Phase 2: Vector asset generation

- Add the pinned schema acquisition and editor-manifest compiler.
- Commit one supported Vector version's generated schema, manifest, and
  provenance.
- Add fixture-based tests for references, unions, maps, nested objects,
  component discriminators, and deterministic output.

Exit criterion: regeneration is deterministic and CI `--check` detects any
schema, compiler, or manifest drift.

### Phase 3: Vector backend

- Add `VectorFormatAdapter` for YAML parsing/rendering and schema validation.
- Add `VectorValidationAdapter` and version-aware availability reporting.
- Add topology diagnostics and normalized native-validation issues.
- Register Vector in format and artifact registries.

Exit criterion: API tests can load, validate, render, and round trip representative
Vector sources, transforms, sinks, global options, VRL, and unknown fields.

### Phase 4: Vector structured editor

- Add manifest-driven named-map collections and component cards.
- Add component IDs, type selection, `inputs`, global options, VRL fields, and
  raw fallback controls.
- Hide Fluent Bit/Fluentd-only panels through capabilities rather than format
  string checks.

Exit criterion: a user can create, open, edit, validate, download, and reopen a
Vector YAML pipeline without data loss.

### Phase 5: Topology and OpAMP workflow

- Add rename/delete impact handling and connection validation.
- Add optional topology visualization based on the native document.
- Add compatible-client filtering and validation status to the provider's
  configuration assignment workflow.

Exit criterion: a validated Vector configuration can be assigned through the
OpAMP server to a Vector consumer, applied, and reported as effective config.

### Phase 6: Additional agents

Prove the adapter boundary with a materially different schema source, such as
the OpenTelemetry Collector or an Elastic agent. Do not claim a multi-agent
architecture complete while adding new formats still requires changes to the
generic API or generic field/collection renderers.

## Test Specification

Backend unit and API coverage must include:

- adapter registration, duplicate keys, unknown formats, and unsupported
  versions;
- deterministic Vector schema import and provenance verification;
- every supported schema composition construct and raw fallback diagnostics;
- YAML parse/render and preservation of unknown fields;
- JSON Schema errors mapped to stable paths;
- graph references, wildcards, rename, delete, self-reference, and cycle cases;
- Vector native validation success, warning, error, timeout, missing binary,
  version mismatch, and oversized output;
- environment interpolation remaining disabled by default;
- old endpoint parity for Fluent Bit and Fluentd; and
- authorization and path containment on load, save, schema, and validation APIs.

Browser unit and Playwright coverage must include:

- format and version switching with empty and populated documents;
- capability-driven panel visibility;
- named component creation for one source, transform, and sink;
- connection selection and reference updates after rename;
- guarded deletion of a referenced component;
- required, optional, enum, bool, number, array, nested object, map, union, code,
  deprecated, and unknown fields;
- load-edit-render-reload round trips;
- raw fallback retention;
- schema and native validation diagnostics; and
- responsive layouts without overlapping controls on desktop and mobile.

All changed Python and JavaScript paths must pass their module-local quality
commands, JavaScript syntax checks, targeted tests, and the repository security
gate before packaging.

## Acceptance Criteria

The Vector addition is complete only when all of the following are true:

1. Given a registered Vector version, the formats API returns its schema,
   editor manifest, serialization choices, and dry-run capability.
2. Given a valid Vector YAML document, parse then render produces a semantically
   equivalent document and retains unknown values.
3. Given a source, transform, and sink, the UI edits their native map keys,
   `type` values, fields, and `inputs` without converting them to plugin arrays.
4. Given a component rename, every exact input reference is updated atomically,
   while wildcard references are reported for review.
5. Given a referenced component deletion, the UI blocks the action until the
   user resolves references or explicitly confirms the displayed impact.
6. Given a structurally invalid value, JSON Schema validation reports a stable
   field path before native validation runs.
7. Given invalid topology or VRL, native Vector validation returns a bounded,
   user-readable diagnostic without leaking configuration secrets.
8. Given no Vector binary, structured editing and schema validation continue
   from bundled assets and native validation clearly reports unavailable.
9. Given a binary/schema version mismatch, generation fails and runtime native
   validation warns or rejects according to configured policy.
10. Given existing Fluent Bit and Fluentd workflows, their API and UI regression
    suites pass without document-shape or output changes.
11. Given a validated saved Vector configuration, the OpAMP server can offer it
    to a compatible Vector consumer and observe effective-config reporting.
12. Given an unsupported schema construct or component, the editor preserves it
    through a raw control and never silently removes it.

## Non-Goals for the First Vector Release

- Replacing Vector's own semantic validator.
- Reimplementing VRL parsing or compilation in JavaScript or Python.
- Supporting TOML and JSON editing before YAML is complete.
- Editing a directory of automatically namespaced Vector fragments.
- Building fleet rollout, live tap, or health dashboards comparable to
  VortexFlow.
- Copying VortexFlow code or introducing React solely for Vector support.
- Defining one normalized agent pipeline that erases native configuration
  semantics.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Vector marks schema generation experimental. | Pin artifacts by version, retain provenance, test schema changes, and keep raw fallback paths. |
| Generated schemas are large and complex. | Compile deterministic editor manifests and lazy-load component schemas. |
| Forms silently omit unsupported constructs. | Emit compiler diagnostics and preserve unsupported values in raw controls. |
| Native validation executes an external binary. | Use argv execution without a shell, timeouts, output limits, path containment, and redacted debug logs. |
| One UI accumulates format checks. | Require capabilities and extension registration; reject new generic-layer format string checks in review. |
| Component rename breaks wildcard inputs. | Update exact references automatically and surface wildcard matches for explicit review. |
| Schema validation disagrees with Vector runtime behavior. | Treat native validation as authoritative and expose both diagnostic sources. |
| A newer editor assigns config to an older agent. | Store version metadata and enforce compatibility policy during assignment. |

## Open Decisions

These decisions can be made during implementation without changing the overall
architecture:

- which Vector version becomes the first supported baseline;
- whether native validation is required or advisory before OpAMP assignment;
- whether comments warrant a round-trip YAML library in a later phase;
- whether schema artifacts are generated only in release tooling or may also be
  generated by an administrator from a locally installed binary; and
- whether the first topology view remains a list or includes a lightweight DAG.

The first supported version should be selected from the versions actually used
by the repository's Vector consumer demonstrations, then pinned in tests and
documentation. It should not be inferred from whichever Vector release happens
to be newest when the server starts.
