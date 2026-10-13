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

# Developer Tools

This page summarizes developer-facing helper scripts in `config-service/dev-tools`.

## Fluent Bit Asset Generator

Script:
- [generate_fluentbit_assets.py](../dev-tools/generate_fluentbit_assets.py)

Detailed design, parsing assumptions, reconciliation rules, report format, and troubleshooting:
- [Fluent Bit Documentation Scraper](./fluentbit_scraper.md)

Purpose:
1. Scrapes Fluent Bit plugin documentation for one or more versions
2. Supports:
   - the Fluent Bit docs website
   - the `fluent/fluent-bit-docs` GitHub repo
   - automatic GitHub → website fallback
3. Generates versioned Fluent Bit catalog JSON artifacts under:
   - `config-service/src/config_service/json-definitions`
4. Runs the post-processing pass that:
   - normalizes plugin names to the real Fluent Bit config `Name`
   - adds shared processor metadata
   - adds router-related fields
   - writes split manifest + per-plugin shard files
5. Optionally updates `config-service/src/config_service/config/catalog-registry.json`
6. Optionally regenerates runtime schemas for the requested versions
7. Reconciles undetermined field metadata with the newest earlier local catalog
8. Writes JSON and Markdown summaries of inherited values, divergence, and incomplete pages
9. Creates a compressed backup of the existing packaged configuration before any generation

The packaged tree under `config-service/src/config_service` is the only generated source of
truth. The tools no longer maintain a duplicate top-level `json-definitions` or `json-schemas`
tree.

The generated catalog layout is versioned and sharded:
1. Top-level manifest file: `json-definitions/fluent-bit-<version>-all-plugins-catalog.json`
2. Version folder: `json-definitions/fluent-bit/<version>/`
3. Plugin-type manifests: `inputs.json`, `filters.json`, `outputs.json`
4. Per-plugin files under `inputs/`, `filters/`, and `outputs/`

Run it:

```bash
cd /mnt/d/dev/opamp
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7
```

The repository developer CLI discovers the same implementation from
`dev-tools/opamp_dev_cli_tools.json`. With no version it resolves the current
stable Fluent Bit release:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets
opamp-dev-cli fluent-resources generate-fluentbit-assets --version 5.0.7
```

Useful examples:

```bash
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7 --source website
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7 --source github --github-ref master
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7 --no-schemas
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7 --no-register
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7 --previous-version 5.0.4
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7 --no-inherit
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7 --backup-dir D:/backups/config-service
python3 config-service/dev-tools/generate_fluentbit_assets.py --remove-version 5.1.3
python3 config-service/dev-tools/generate_fluentbit_assets.py --remove-version 5.0.4 --replacement-default 4.2.4
```

Notes:
1. When no generation or removal option is provided, the current stable Fluent Bit release is resolved from GitHub before any repository mutation
2. The website root is resolved from `https://docs.fluentbit.io/manual/<version>/administration/configuring-fluent-bit`
3. If the exact patch path does not exist, the tool falls back to the series path and then the unversioned manual
4. GitHub mode resolves `.gitbook.yaml` first so plugin names come from the canonical docs mapping rather than page slugs
5. By default, missing metadata is inherited from the nearest earlier registered catalog and all inherited or divergent values are reported
6. Reports are written under `config-service/reports/fluentbit` unless `--summary-dir` overrides the location
7. Before the first requested generation or removal change, one atomic ZIP snapshot of packaged `config`, `json-definitions`, and `json-schemas` is written under `config-service/backups` unless `--backup-dir` overrides it
8. `--remove-version` deletes the named version's canonical definitions, schema artifacts, and registry entries, then writes JSON and Markdown removal reports
9. Removing a current default requires `--replacement-default` naming a version already registered in every affected registry
10. Backup failure aborts the run before generation or removal starts; backups are retained until a maintainer removes them

## Fluent Bit Schema Quick Reference Generator

Script:
- [generate_fluentbit_schema_quick_reference.py](../dev-tools/quick-references/generate_fluentbit_schema_quick_reference.py)

Purpose:
1. Reads the local Fluent Bit JSON schema files
2. Generates Markdown quick references for:
   - `env` environment variables
   - `upstream_servers` upstream server groups
   - pipeline plugins
3. Produces grouped pipeline sections for:
   - `inputs`
   - `filters`
   - `outputs`
4. Includes:
   - alphabetical plugin jump lists
   - plugin anchors
   - mandatory flags
   - default values
   - descriptions
   - hyperlinks to Fluent Bit documentation

The schema input files can be either direct JSON payloads or manifest files that point to
versioned shard trees such as `json-schemas/fluentbit/3.2.10/inputs/*.json`. Individual
plugin shard files may use JSON Schema `$ref` to shared version-local fragments such as
`json-schemas/fluentbit/3.2.10/processors.json`.

Inputs:
1. [fluentbit-3.2.10-config-schema.json](../src/config_service/json-schemas/fluentbit-3.2.10-config-schema.json)
2. [fluentbit-4.2.4-config-schema.json](../src/config_service/json-schemas/fluentbit-4.2.4-config-schema.json)
3. [fluentbit-5.0.4-config-schema.json](../src/config_service/json-schemas/fluentbit-5.0.4-config-schema.json)

Outputs:
1. [fluentbit-3-2-10-schema-quick-reference.md](../../quick-references/fluentbit-3-2-10-schema-quick-reference.md)
2. [fluentbit-4-2-4-schema-quick-reference.md](../../quick-references/fluentbit-4-2-4-schema-quick-reference.md)
3. [fluentbit-5-0-4-schema-quick-reference.md](../../quick-references/fluentbit-5-0-4-schema-quick-reference.md)

Run it:

```bash
cd /mnt/d/dev/opamp
python3 config-service/dev-tools/quick-references/generate_fluentbit_schema_quick_reference.py
```

Optional:

```bash
python3 config-service/dev-tools/quick-references/generate_fluentbit_schema_quick_reference.py --help
python3 config-service/dev-tools/quick-references/generate_fluentbit_schema_quick_reference.py --version 4.2.4
python3 config-service/dev-tools/quick-references/generate_fluentbit_schema_quick_reference.py --source-dir config-service/src/config_service/json-schemas --output-dir quick-references
```

What to expect:
1. The script overwrites the generated Markdown file
2. The output is deterministic for the current schema contents
3. Any formatting updates should be made in the generator, then regenerated

Recommended verification:

```bash
python3 -m ruff check config-service/dev-tools/quick-references/generate_fluentbit_schema_quick_reference.py
```

When to use it:
1. After schema regeneration for Fluent Bit `3.2.10`, `4.2.4`, or `5.0.4`
2. After adjusting schema metadata such as descriptions, defaults, or required flags
3. When refreshing the quick references in `quick-references`

## Fluent Bit Plugin Attribute Reference Generator

Script:
- [generate_fluentbit_plugin_attribute_reference.py](../dev-tools/quick-references/generate_fluentbit_plugin_attribute_reference.py)

Purpose:
1. Reads the local Fluent Bit catalog JSON files
2. Generates Markdown attribute reference files for each Fluent Bit version
3. Produces grouped sections for:
   - `inputs`
   - `filters`
   - `outputs`

The catalog input files can be either direct JSON payloads or manifest files that point to
versioned shard trees such as `json-definitions/fluent-bit/3.2.10/outputs/*.json`.

Inputs:
1. [fluent-bit-3.2.10-all-plugins-catalog.json](../src/config_service/json-definitions/fluent-bit-3.2.10-all-plugins-catalog.json)
2. [fluent-bit-4.2.4-all-plugins-catalog.json](../src/config_service/json-definitions/fluent-bit-4.2.4-all-plugins-catalog.json)
3. [fluent-bit-5.0.4-all-plugins-catalog.json](../src/config_service/json-definitions/fluent-bit-5.0.4-all-plugins-catalog.json)

Outputs:
1. [fluentbit-3-2-10-plugin-attribute-reference.md](../../quick-references/fluentbit-3-2-10-plugin-attribute-reference.md)
2. [fluentbit-4-2-4-plugin-attribute-reference.md](../../quick-references/fluentbit-4-2-4-plugin-attribute-reference.md)
3. [fluentbit-5-0-4-plugin-attribute-reference.md](../../quick-references/fluentbit-5-0-4-plugin-attribute-reference.md)

Run it:

```bash
cd /mnt/d/dev/opamp
python3 config-service/dev-tools/quick-references/generate_fluentbit_plugin_attribute_reference.py
```

Optional:

```bash
python3 config-service/dev-tools/quick-references/generate_fluentbit_plugin_attribute_reference.py --help
python3 config-service/dev-tools/quick-references/generate_fluentbit_plugin_attribute_reference.py --source-dir config-service/src/config_service/json-definitions --output-dir quick-references
```

## Fluent Bit Markdown Generator

Script:
- [generate_fluentbit_markdown.py](../dev-tools/generate_fluentbit_markdown.py)

Purpose:
1. Regenerates human-readable Fluent Bit Markdown references from local generated artifacts
2. Runs:
   - the schema quick-reference generator
   - the plugin attribute reference generator
3. Uses the already-generated local schema/catalog JSON artifacts as the source of truth

Run it:

```bash
cd /mnt/d/dev/opamp
python3 config-service/dev-tools/generate_fluentbit_markdown.py --version 5.0.7
```

Optional:

```bash
python3 config-service/dev-tools/generate_fluentbit_markdown.py --version 5.0.7 --skip-attribute-reference
python3 config-service/dev-tools/generate_fluentbit_markdown.py --version 5.0.7 --skip-schema-reference
```
