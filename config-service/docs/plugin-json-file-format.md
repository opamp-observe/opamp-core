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

# Plugin JSON File Format

## Purpose
`config-service` uses two related JSON formats for plugin metadata:

1. Source plugin definition files under `config-service/src/config_service/json-definitions/<engine>/<version>/<section>/`
2. Generated runtime schema shard files under `config-service/src/config_service/json-schemas/<config_type>/<version>/<section>/`

The packaged `config-service/src/config_service` tree is the single source used by repository
tools and installed runtime code.

This guide explains what each attribute means, which ones are mandatory, how data types are interpreted, and how validation works.

## Which file is the source of truth?
For plugin fields, the source of truth is the plugin definition file in `json-definitions`.

That source metadata drives:
1. UI field lists and required markers
2. Runtime schema compilation
3. Backend semantic validation
4. Rule-engine checks

Generated files in `json-schemas` are derived artifacts. They are useful for schema-driven rendering and documentation, but they are not the primary place to edit required flags or field metadata.

## `json-definitions` vs `json-schemas`
These two trees serve different purposes and should not be edited interchangeably.

| Tree | Role | Edit directly? | Used for |
| --- | --- | --- | --- |
| `config-service/src/config_service/json-definitions/...` | Source metadata authored by maintainers | Yes | UI field metadata, required flags, validation hints, schema compilation |
| `config-service/src/config_service/json-schemas/...` | Generated runtime JSON Schema artifacts | Usually no | Schema-driven rendering, schema inspection, generated references |

### `json-definitions`
Use `json-definitions` when you want to change what a plugin means.

Typical changes:

1. mark a field required or optional
2. change `description`
3. change `reference`
4. change `data_type`
5. change `validation_rule`
6. add/remove a field
7. change parser-reference behavior

### `json-schemas`
Use `json-schemas` when you want to inspect the compiled result.

Typical contents:

1. JSON Schema `type`
2. JSON Schema `required`
3. plugin `name.const`
4. copied documentation metadata such as `x-doc-reference`
5. copied catalog hints such as `x-config-data-type`
6. generated `$ref` links such as shared Fluent Bit `processors.json`

### Practical rule
If you are asking “should this field be mandatory in the UI or backend?”, update `json-definitions`.

If you are asking “what schema was generated from the catalog?”, inspect `json-schemas`.

## Source plugin definition files
Typical examples:

1. `config-service/src/config_service/json-definitions/fluent-bit/5.0.4/inputs/tail.json`
2. `config-service/src/config_service/json-definitions/fluent-bit/5.0.4/outputs/s3.json`
3. `config-service/src/config_service/json-definitions/fluentd/1.19/outputs/copy.json`

### Top-level attributes
| Attribute | Type | Mandatory | Meaning |
| --- | --- | --- | --- |
| `title` | `string` | No, but strongly recommended | Human-readable plugin name shown in docs/UI. |
| `doc_url` | `string` | No, but strongly recommended | Main upstream documentation page for the plugin. |
| `description` | `string` | No | Extra plugin-level description. Common on Fluentd plugin files. |
| `fields` | `array<object>` | Yes | List of configurable plugin attributes. |
| `allowed_children` | `array<object>` | No | Nested section support, mainly for Fluentd. |
| `directive_argument` | `object` | No | Pseudo-field for directives such as Fluentd `match`. |

### `fields[]` attributes
Every object inside `fields` represents one plugin attribute such as `path`, `match`, or `buffer_chunk_size`.

| Attribute | Type | Mandatory | Meaning |
| --- | --- | --- | --- |
| `name` | `string` | Yes | Exact configuration key written into the generated config. |
| `required` | `boolean` | Yes | Marks the field as mandatory for UI and backend validation. |
| `description` | `string` | Yes | User-facing help text. |
| `reference` | `string` | Yes | Upstream reference URL, usually anchored to the parameter section. |
| `data_type` | `string` | Yes | Logical type used by UI and validation. |
| `validation_rule` | `object` or `null` | No | Additional rule metadata for backend checks. |
| `default` | any JSON value | No | Default value shown/documented for the field. |
| `enum_options` | `array<string>` | No | Explicit allowed values for enum-like fields. Also used as a fallback source for schema `enum` values when `validation_rule.kind` is `enum` and `validation_rule.values` is omitted. |
| `references_parser` | `boolean` | No | Marks fields whose value should match a known parser name. |

### `directive_argument` attributes
`directive_argument` uses the same contract as a field-like object and must include:

1. `name`
2. `required`
3. `description`
4. `reference`
5. `data_type`

It may also include:

1. `validation_rule`
2. `default`
3. `enum_options`

### `allowed_children[]` attributes
These define nested child sections for plugins that support them.

| Attribute | Type | Mandatory | Meaning |
| --- | --- | --- | --- |
| `section` | `string` | Yes | Nested section name, for example `store` or `parse`. |
| `cardinality` | `object` | No | Minimum/maximum child count constraints. |

If `cardinality` is present, it usually contains:

1. `minimum`: `integer` or `null`
2. `maximum`: `integer` or `null`

## Supported `data_type` values
The catalog and validation layer currently understand these logical data types:

| `data_type` | Expected runtime shape |
| --- | --- |
| `string` | string |
| `code` | string |
| `duration` | string |
| `time` | string or non-negative integer depending on validator context |
| `size` | string |
| `integer` | integer |
| `number` | number |
| `float` | number |
| `boolean` | boolean |
| `array` | array |
| `list` | array |
| `object` | object |
| `map` | object |
| `hash` | object |
| `enum` | string, usually with `enum_options` |

## How `validation_rule` works
`validation_rule` adds backend validation metadata beyond the base `data_type`.

Common forms include:

| Kind | Typical payload | Purpose |
| --- | --- | --- |
| `boolean` | `{ "kind": "boolean" }` | Enforces boolean values. |
| `integer` | `{ "kind": "integer" }` | Documents integer intent in source metadata. |
| `list` | `{ "kind": "list" }` | Documents that the field is list-shaped, typically paired with `data_type: "list"` for array-backed fields such as Fluentd `chunk_keys` or CSV `fields`. |
| `range` | `{ "kind": "range", "min": 0, "max": 10 }` | Enforces numeric bounds. |
| `regex` | `{ "kind": "regex", "pattern": "..." }` | Enforces a pattern. |
| `regex_string` | `{ "kind": "regex_string", "pattern": "..." }` | String-specific regex validation. |
| `duration` | `{ "kind": "duration" }` | Enforces compact duration strings such as `250ms`, `5s`, `1m`, or `2h` using `^\\d+(ns|us|ms|s|m|h|d)?$`. |
| `size` | `{ "kind": "size" }` | Enforces Fluent Bit size strings such as `32k` or `10M`; see https://docs.fluentbit.io/manual/administration/configuring-fluent-bit#unit-sizes |
| `enum` | `{ "kind": "enum", "values": [...] }` | Documents allowed values, usually paired with `enum_options`. If `values` is omitted, schema generation falls back to the field's `enum_options` when present. |

Example duration field:

```json
{
  "name": "scrape_interval",
  "required": false,
  "description": "The interval to scrape metrics from the target.",
  "reference": "https://docs.fluentbit.io/manual/data-pipeline/inputs/nginx#configuration-parameters",
  "default": "5s",
  "data_type": "duration",
  "validation_rule": {
    "kind": "duration"
  }
}
```

Important nuance:

1. Not every `validation_rule` becomes a native JSON Schema keyword.
2. Runtime schema compilation mainly carries forward `type`, `description`, `enum`, `default`, and `x-*` metadata.
3. Backend semantic validation and rule adapters enforce the richer rule set.
4. Some rule kinds such as `list` are currently descriptive catalog metadata rather than a dedicated standalone rule-adapter branch.
5. For enum-like fields, runtime schema generation prefers `validation_rule.values` when `kind` is `enum`, and otherwise falls back to `enum_options` if available.

## Generated runtime schema shard files
Typical examples:

1. `config-service/src/config_service/json-schemas/fluentbit/5.0.4/inputs/tail.json`
2. `config-service/src/config_service/json-schemas/fluentbit/5.0.4/outputs/s3.json`
3. `config-service/src/config_service/json-schemas/fluentd/1.19/outputs/copy.json`

These files are JSON Schema fragments for one plugin variant.

### Top-level schema attributes
| Attribute | Type | Mandatory | Meaning |
| --- | --- | --- | --- |
| `type` | `string` | Yes | Usually `object`. |
| `title` | `string` | No | Human-readable plugin title. |
| `properties` | `object` | Yes | Schema for each plugin property. |
| `required` | `array<string>` | Yes | JSON Schema required list. Always includes `name`. |
| `additionalProperties` | `boolean` | Yes | Whether undeclared keys are allowed. |
| `allOf` | `array<object>` | No | Extra constraints, for example directive-argument alias handling. |

### Top-level schema property keys
Common properties on a plugin shard:

| Property key | Type | Mandatory | Meaning |
| --- | --- | --- | --- |
| `name` | schema object | Yes | Plugin identifier; compiled with a fixed `const` value. |
| `<field name>` | schema object | No | One entry per catalog field. |
| `children` | schema object | No | Nested sections, when the plugin supports them. |
| `processors` | schema object or `$ref` | No | Fluent Bit processors metadata for `inputs` and `outputs`. |
| `route` | schema object | No | Fluent Bit route metadata for supported input plugins. |
| `_meta` | schema object | No | Comment/annotation metadata used by the editor. |

### Attributes inside each field schema
| Attribute | Type | Mandatory | Meaning |
| --- | --- | --- | --- |
| `type` | `string` | Yes | JSON Schema type mapped from catalog `data_type`. |
| `description` | `string` | No | Help text copied from the catalog. |
| `enum` | `array` | No | Allowed values for enum-like fields. |
| `default` | any JSON value | No | Default value copied from the catalog. |
| `x-doc-reference` | `string` | No | Upstream docs link copied from `reference`. |
| `x-doc-required` | `boolean` | No | Copy of catalog `required`, mainly for documentation helpers. |
| `x-config-data-type` | `string` | No | Original logical `data_type` from the catalog. |
| `x-references-parser` | `boolean` | No | Copy of `references_parser`. |
| `$ref` | `string` | No | External schema reference, currently used for shared processor definitions. |

## Mandatory fields: what actually makes a field required?
There are three related representations of “required”:

1. Source catalog field flag: `fields[].required`
2. Generated schema metadata flag: `x-doc-required`
3. Generated JSON Schema enforcement list: top-level `required[]`

The source catalog field flag is the authoritative one.

Effects:

1. The UI uses catalog field metadata to decide whether to show a field as required.
2. Schema compilation mirrors required fields into the plugin shard `required[]`.
3. Backend semantic validation reports missing required fields from the catalog definition.
4. Rule-engine validation also mirrors catalog-required checks.

If you want to change whether a plugin attribute is mandatory, update the plugin definition file in `json-definitions`, then regenerate artifacts if needed.

## Validation flow end to end
### 1. Catalog integrity validation
When a plugin definition file is loaded, the catalog loader requires each field-like object to include:

1. `name`
2. `required`
3. `description`
4. `reference`
5. `data_type`

If any are missing, catalog loading/validation fails.

### 2. Schema compilation
The schema compiler converts catalog metadata into per-plugin schema shards:

1. `data_type` becomes JSON Schema `type`
2. `enum_options` becomes JSON Schema `enum`
3. `required=true` becomes schema `required[]`
4. Documentation metadata is copied into `x-*` fields

### 3. Backend semantic validation
When a config is validated, the backend checks more than just JSON Schema:

1. missing required fields
2. unknown fields
3. parser references
4. `match`/`match_regex` selector presence where applicable
5. Fluent Bit processors structure
6. Fluent Bit route structure
7. Fluentd nested child-section structure

### 4. Rule-engine validation
Rule adapters then enforce catalog-derived constraints such as:

1. data type compatibility
2. numeric ranges
3. regex pattern rules
4. boolean-only constraints

## Editing guidance
### To change field help text, docs links, defaults, required flags, or logical types
Edit the source plugin definition file under `json-definitions`.

### To change compiled shard layout
Edit the schema generation/compiler code, then regenerate runtime schemas.

### Do not edit generated schema shards as your primary change
Direct edits under `json-schemas` may be overwritten by regeneration and may not change UI behavior if the source catalog still says the field is required.

## Related files
1. `config-service/docs/catalog-management.md`
2. `config-service/docs/dev-tools.md`
3. `config-service/dev-tools/generate_runtime_schemas.py`
4. `config-service/src/config_service/services/catalog_service.py`
5. `config-service/src/config_service/services/schema_service.py`
6. `config-service/src/config_service/services/validation_service.py`
