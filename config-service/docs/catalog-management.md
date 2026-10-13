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

# Catalog Management

## Purpose
Catalogs define plugin metadata used for:
1. Dynamic UI generation
2. Required field enforcement
3. Field typing and validation rule hints

## Catalog location
- `config-service/src/config_service/json-definitions/*.json`
- `config-service/src/config_service/json-definitions/fluent-bit/<version>/`
- `config-service/src/config_service/json-definitions/fluentd/<version>/`
- Registered in `config-service/src/config_service/config/catalog-registry.json`
- Service/system option definitions are registered in `config-service/src/config_service/config/service-registry.json`
- Parser definitions are registered in `config-service/src/config_service/config/parser-registry.json`
- Generated runtime schemas are written to `config-service/src/config_service/json-schemas/*.json`
- Generated runtime schema shards live under `config-service/src/config_service/json-schemas/<config_type>/<version>/`

This packaged source tree is canonical. Developer generators do not write duplicate top-level
`config-service/json-definitions` or `config-service/json-schemas` trees.

Large catalog and schema files are stored as manifest files. The public top-level file
name remains stable, but the manifest now points to:
1. a versioned base file
2. one manifest per plugin section (`inputs`, `filters`, `outputs`)
3. one JSON file per plugin under the matching section folder

Runtime loaders and developer tools assemble those shards automatically.

## Expected plugin field metadata
Each field should include:
1. `name`
2. `required`
3. `description`
4. `reference`
5. `data_type`
6. Optional `validation_rule`
7. Optional `default`

## Expected catalog structure
Each engine-specific catalog file now uses a direct plugin map:

```json
{
  "engine": "fluentbit",
  "plugins": {
    "inputs": {},
    "filters": {},
    "outputs": {}
  }
}
```

Notes:
1. Catalog files are already split by engine, so there is no extra `plugins.fluentbit` or `plugins.fluentd` nesting.
2. Fluent Bit and Fluentd both use the same `plugins.inputs|filters|outputs` shape.
3. Engine-specific metadata such as `nested_sections` remains at the catalog top level where needed.

## Fluent Bit processor metadata
Fluent Bit processor definitions are stored as shared catalog metadata under:
1. `common.processors`
2. `common.route`

This keeps shared Fluent Bit editor metadata versioned but avoids duplicating the same schema fragments inside every plugin.

Current model:
1. Processors are attachable to Fluent Bit `inputs` and `outputs`
2. Processor definitions are grouped by signal type (`logs`, `metrics`, `traces`)
3. Log processors can additionally reuse filter plugin definitions as "filters as processors"
4. Route definitions are attachable only to Fluent Bit `inputs`

## Fluent Bit route metadata
Fluent Bit conditional routing metadata is stored under `common.route`.

This lets the UI and schema layer:
1. add a nested Route panel only for supported Fluent Bit input plugins
2. expose supported signal groupings such as `logs`, `metrics`, `traces`, and `any`
3. describe supported condition contexts and operators
4. keep the internal editor model as `route` while rendering native Fluent Bit YAML back as `routes`

## Fluent Bit parser metadata
Fluent Bit parser definitions are versioned separately from plugin catalogs:
1. Parser definition files live under `config-service/src/config_service/json-definitions/fluent-bit-*-parser-options.json`
2. They are registered in `config-service/src/config_service/config/parser-registry.json`
3. Input plugin fields that point at parsers use `references_parser: true`

This lets the UI build a dedicated Parsers section and lets validation match parser references against:
1. user-defined parsers in `config.parsers`
2. known built-in Fluent Bit parser names for that version

## Add a new version
1. Add the top-level JSON catalog manifest under `config-service/src/config_service/json-definitions/`
2. Add the matching per-version shard directory under `config-service/src/config_service/json-definitions/<engine>/<version>/`
3. Add version entry under the correct engine in `catalog-registry.json`
4. Add matching service definition entry in `service-registry.json`
5. Add matching parser definition entry in `parser-registry.json` when the engine supports parser definitions
6. Optionally update `default_versions`
7. Restart backend (or use dev reload flow) and verify:
   - `GET /config-service/api/v1/versions?config_type=<engine>`
   - `GET /config-service/api/v1/parser-options/{version}` for Fluent Bit
   - `POST /config-service/api/v1/catalog/{version}/validate`

For large `all-plugins-catalog.json` files, keep the top-level file as the registry
target and place the generated shards in version folders such as:
1. `config-service/src/config_service/json-definitions/fluent-bit/3.2.10/inputs/tail.json`
2. `config-service/src/config_service/json-definitions/fluent-bit/3.2.10/filters/grep.json`
3. `config-service/src/config_service/json-definitions/fluent-bit/3.2.10/outputs/stdout.json`
4. `config-service/src/config_service/json-schemas/fluentbit/3.2.10/inputs/tail.json`
5. `config-service/src/config_service/json-schemas/fluentbit/3.2.10/outputs/stdout.json`
6. `config-service/src/config_service/json-schemas/fluentbit/3.2.10/processors.json`

This keeps editors responsive while preserving the registry path.

Fluent Bit schema plugin shards may either:
1. include shared `processors` details inline
2. or reference the version-local shared file `processors.json` via JSON Schema `$ref`

## Fluentd artifacts
Generated Fluentd catalog and service files currently live at:
1. `config-service/src/config_service/json-definitions/fluentd-1.8-all-plugins-catalog.json`
2. `config-service/src/config_service/json-definitions/fluentd-1.16-all-plugins-catalog.json`
3. `config-service/src/config_service/json-definitions/fluentd-1.19-all-plugins-catalog.json`
4. `config-service/src/config_service/json-definitions/fluentd-1.8-service-options.json`
5. `config-service/src/config_service/json-definitions/fluentd-1.16-service-options.json`
6. `config-service/src/config_service/json-definitions/fluentd-1.19-service-options.json`

These are generated by:
1. `config-service/dev-tools/generate_fluentd_assets.py`
2. `config-service/dev-tools/generate_runtime_schemas.py`

## Validate catalog integrity
Endpoint:
- `POST /config-service/api/v1/catalog/{version}/validate`

Checks include:
1. Required top-level catalog keys
2. Required `engine` key presence
3. Plugin section presence (`inputs`, `filters`, `outputs`)
4. Required field metadata presence
5. Fluentd nested-section metadata integrity when `engine=fluentd`

## Backward compatibility guidance
1. Keep old version files immutable after release.
2. Add new versions as new files.
3. Use `version_overrides` in validation registry for version-specific rule behavior.
