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

# Fluent Bit documentation scraper

## Purpose

The Fluent Bit documentation scraper builds the versioned plugin catalog used by the
config-service UI, validators, schema compiler, and reference generators. It retrieves
input, filter, and output documentation, extracts plugin fields, enriches the result with
config-service metadata, and writes sharded JSON artifacts.

The current implementation is a one-pass generator. Discovery, retrieval, parsing,
reconciliation, enrichment, artifact writing, and optional schema compilation happen in one
command. It does not yet create a separately editable discovery plan before retrieval.

The command-line entry point is
[`generate_fluentbit_assets.py`](../dev-tools/generate_fluentbit_assets.py). Its main parsing
implementation is
[`fluentbit_docs_support.py`](../src/config_service/fluentbit_docs_support.py), and comparison
with an earlier catalog is handled by
[`fluentbit_catalog_reconciliation.py`](../src/config_service/fluentbit_catalog_reconciliation.py).

## End-to-end flow

```text
requested version
    |
    +--> atomically back up the current packaged configuration tree
    |
    +--> resolve documentation source and version/ref
    |
    +--> discover input, filter, and output pages
    |
    +--> parse configuration parameter tables
    |
    +--> compare with the newest earlier local catalog
    |       +--> carry forward undetermined metadata
    |       +--> flag incomplete pages
    |       +--> record differences without hiding them
    |
    +--> normalize plugin names and add processors/router metadata
    |
    +--> write catalog manifests and per-plugin shards
    |
    +--> optionally register the version and compile runtime schemas
    |
    +--> write JSON and Markdown review summaries
```

## Running the scraper

From the repository root:

```bash
python3 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7
```

The consolidated developer CLI discovers this generator from the Config
Service component manifest. Omit `--version` to resolve and generate the
current stable Fluent Bit release:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets
opamp-dev-cli fluent-resources generate-fluentbit-assets --version 5.0.7
```

On Windows, use an installed interpreter or launcher, for example:

```powershell
py -3.11 config-service/dev-tools/generate_fluentbit_assets.py --version 5.0.7
```

The command logs at debug level so source selection, fallback behavior, page retrieval,
normalization, and artifact generation can be investigated from one run.

Useful options:

| Option | Meaning |
| --- | --- |
| `--version VERSION` | Version to generate. Repeat the option to generate multiple versions. Omit both generation and removal options to resolve the current stable release. |
| `--remove-version VERSION` | Remove one version's canonical catalogs, service/parser definitions, schemas, and registry entries. This is mutually exclusive with `--version`. |
| `--replacement-default VERSION` | Registered version that becomes the default when removing a current default. |
| `--source auto` | Try the GitHub documentation repository first, then the website. This is the default. |
| `--source github` | Read Markdown from `fluent/fluent-bit-docs`. |
| `--source website` | Parse rendered pages from `docs.fluentbit.io`. |
| `--github-ref REF` | Override GitHub tag, branch, or commit resolution. |
| `--previous-version VERSION` | Use an explicit local catalog as the reconciliation baseline. |
| `--no-inherit` | Disable all previous-catalog carry-forward behavior. A summary is still produced. |
| `--summary-dir PATH` | Change the JSON and Markdown report directory. |
| `--backup-dir PATH` | Change the directory used for the mandatory pre-change ZIP backup. |
| `--no-register` | Do not update `src/config_service/config/catalog-registry.json`. |
| `--no-schemas` | Do not compile runtime JSON Schema artifacts. |
| `--timeout SECONDS` | Set the HTTP request timeout. |

Example with an explicit baseline and review-report directory:

```bash
python3 config-service/dev-tools/generate_fluentbit_assets.py \
  --version 5.0.7 \
  --previous-version 5.0.4 \
  --summary-dir config-service/reports/fluentbit
```

## Removing a version

Use `--remove-version` to remove a generated Fluent Bit version from the canonical packaged
tree. The operation removes:

- The catalog manifest and `json-definitions/fluent-bit/<version>/` shard tree.
- Matching service and parser option definitions when present.
- The runtime schema manifest and `json-schemas/fluentbit/<version>/` shard tree.
- The version's entries from the catalog, service, and parser registries.

For example:

```powershell
py -3.11 config-service/dev-tools/generate_fluentbit_assets.py --remove-version 5.1.3
```

The version must use semantic version form. An unknown version fails without changing the
configuration. If the version is a current default in any registry, provide a replacement that
is already registered in every affected registry:

```powershell
py -3.11 config-service/dev-tools/generate_fluentbit_assets.py --remove-version 5.0.4 --replacement-default 4.2.4
```

As with generation, a compressed configuration backup is completed before removal starts. A
backup failure prevents all deletion. Successful removal writes JSON and Markdown audit reports
under `config-service/reports/fluentbit` unless `--summary-dir` overrides the location. The
reports identify the backup, removed paths, registry entries, and any default-version change.

## Documentation source resolution

### Automatic source mode

`--source auto` first attempts the GitHub Markdown source. Any exception while resolving the
GitHub ref, mappings, section URLs, or pages causes a warning and a fallback to website mode.
The fallback applies to the complete scrape, not to individual pages.

### GitHub mode

GitHub mode resolves `.gitbook.yaml` in `fluent/fluent-bit-docs`. Unless `--github-ref` is
provided, refs are attempted in this order:

1. `v<exact version>`
2. `<exact version>`
3. `v<major.minor>`
4. `<major.minor>`
5. `master`
6. `main`

Redirect entries such as `input/stdin`, `filter/grep`, and `output/stdout` provide the native
plugin name and Markdown path. This is preferable to deriving configuration names from page
slugs because names such as `stdout` can be documented under a page named
`standard-output.md`.

GitHub mode still resolves the website section roots so generated `doc_url` and field
`reference` values point to public documentation rather than raw GitHub content.

### Website mode

Website mode attempts these manual roots:

1. `https://docs.fluentbit.io/manual/<exact version>`
2. `https://docs.fluentbit.io/manual/<major.minor>`
3. `https://docs.fluentbit.io/manual`

It resolves the configuring-Fluent-Bit page and then discovers the inputs, filters, and outputs
indexes. Both `data-pipeline/<section>` and older `pipeline/<section>` layouts are supported.
Plugin links must be direct children of the relevant section URL; deeper links are ignored.

## Expected plugin page pattern

### Markdown pages

A normally parsed Markdown page has:

1. A level-one title beginning with `# `.
2. Optional introductory paragraphs before the configuration section.
3. A level-two heading spelled `## Configuration parameters`.
4. A Markdown pipe table immediately following that heading.
5. At least `Key` and `Description` columns.
6. Optional `Default` and `Required` columns.

The heading comparison is currently case-sensitive in Markdown mode. The table parser stops at
the first non-table line after table capture starts. Configuration tables placed under another
heading, written as definition lists, split into multiple tables, or containing multiline rows
will not be fully extracted.

### Rendered website pages

The website parser expects:

1. An `h1` title.
2. An `h2` or `h3` whose normalized text is `Configuration parameters`.
3. GitBook table accessibility roles: `row`, `columnheader`, and `cell`.

Table collection stops when another `h2` or `h3` is encountered. A site template change that
removes these roles or changes the heading will usually produce no fields and therefore a review
warning.

## Plugin-name detection

The parser tries to identify the actual value accepted by Fluent Bit's `Name` setting from page
text. It recognizes:

1. Runtime log fragments such as `[input:tail:tail.0]`.
2. Configuration fragments such as `[INPUT] Name tail`.
3. Command-line examples such as `-i tail`, `-F grep`, and `-o stdout`.

When no native name is found, website mode falls back to the final URL path component. GitHub
mode uses the `.gitbook.yaml` redirect name. The later enrichment pass checks page text again,
normalizes names, and reports collisions instead of overwriting colliding plugins.

## Field extraction and inference

Each configuration table row becomes one catalog `fields[]` entry. Column names are matched
case-insensitively after extraction.

| Catalog attribute | Source or inference |
| --- | --- |
| `name` | `Key` column, with Markdown code formatting removed. |
| `description` | `Description` column. |
| `reference` | Plugin URL plus `#configuration-parameters`. |
| `required` | True only for `yes`, `true`, or `required` in a `Required` column. |
| `default` | Parsed from `Default`; booleans, integers, and decimal numbers become JSON primitives. |
| `data_type` | Inferred from the parsed default, description, field name, and known value patterns. |
| `validation_rule` | Added when the inferred type has a supported validation rule. |
| `references_parser` | Set for `parser`, `docker_mode_parser`, and names ending in `.parser`. |

Current type inference recognizes:

- Boolean defaults.
- Integer and decimal defaults.
- Fluent Bit unit-size values and descriptions mentioning the Unit Size specification.
- Duration suffixes such as `ns`, `us`, `ms`, `s`, `m`, `h`, and `d`.
- Descriptions containing `Possible values:` as enum-like values.
- Parser-reference field names.

When none of those signals is present, the field is initially typed as `string`. This is a weak
inference rather than proof that the field changed to a string.

## Previous-catalog reconciliation

### Baseline selection

Unless `--no-inherit` is supplied, the generator reads the local catalog registry and selects
the greatest semantic version lower than the target. For example, target `5.0.10` selects
`5.0.9` ahead of `5.0.4`. Version comparison is numeric rather than lexical.

`--previous-version` overrides automatic selection. The explicit version must exist in
`config-service/src/config_service/json-definitions`.

An unavailable explicitly requested catalog is an error. An automatically selected registry
entry whose artifact is unavailable produces a warning and continues without inheritance.

The registry and catalogs are read only from the canonical packaged source tree:

- `config-service/src/config_service/config/catalog-registry.json`
- `config-service/src/config_service/json-definitions`

The former top-level `config-service/json-definitions` tree is not generated or consulted.

### Matching

Catalogs are matched by section, plugin name, and field name. A rename that has not yet been
normalized can appear as one removed plugin and one added plugin. Such cases require review in
the summary.

### Attribute carry-forward rules

The scraped value wins when the documentation yielded a meaningful value. Earlier values are
used only for metadata the scraper could not determine reliably:

| Situation | Reconciliation behavior |
| --- | --- |
| Attribute absent, empty, or null | Copy the earlier non-empty value. |
| No `Required` table column | Copy the earlier `required` value. |
| New type is the default `string`, while the prior type was more specific and the current row has no type evidence | Copy the earlier `data_type`. |
| Default, validation rule, enum options, or parser-reference marker cannot be inferred | Copy the earlier value when present. |
| Both versions contain different meaningful values | Keep the current value and record a divergence. |

Every copied value records the source version and one of these reasons:

- `missing_attribute`
- `required_column_missing`
- `weak_type_inference`
- `incomplete_page`

### Missing fields

Field-level carry-forward depends on page confidence:

- If the new page was parsed successfully, a prior-only field is not restored. It may have been
  deliberately removed upstream, so it is recorded as `field_not_documented`.
- If the page is incomplete or structurally unexpected, prior-only fields are retained and
  recorded with reason `incomplete_page`.

This rule prevents a valid upstream removal from being silently undone while protecting the
catalog from accidental data loss caused by a documentation layout change.

### Incomplete pages and embedded review markers

A page is incomplete when either condition is true:

1. Its extraction status is not `ok`.
2. Its extracted table headers do not include both `Key` and `Description`.

The plugin's `extraction` object then receives:

```json
{
  "review_required": true,
  "review_comment": "REVIEW REQUIRED: The documentation page did not expose the expected configuration parameter table. Fields from the previous catalog were retained where available; verify the page reference and table section before accepting this catalog."
}
```

JSON does not support comments, so `review_comment` is explicit metadata rather than invalid
comment syntax. It remains close to the affected plugin and is repeated in the summary report.

## Divergence and completeness reports

Every run writes two equivalent reports by default:

- `config-service/reports/fluentbit/fluentbit_<version>_scrape_summary.json`
- `config-service/reports/fluentbit/fluentbit_<version>_scrape_summary.md`

Dots and other punctuation in the version become underscores, keeping Markdown filenames in
lowercase snake case.

The reports contain:

1. Target and previous version identifiers.
2. Counts for incomplete pages, inherited values, divergences, added plugins, and added fields.
3. Pages requiring manual review.
4. Every value carried forward, including its reason and prior version.
5. Plugin additions and apparent removals.
6. Field additions and fields no longer documented.
7. Plugin or field attributes whose meaningful current and previous values differ.

The summary is intentionally advisory. Divergence does not fail generation because documentation
changes can be legitimate. Incomplete pages are similarly retained for review so one unusual
plugin page does not prevent every other plugin from being generated.

## Enrichment and generated files

After reconciliation, `add_fluentbit_processors.py`:

1. Normalizes plugin names from their documentation evidence.
2. Adds shared processor definitions.
3. Adds input `tag` and filter/output `match` routing metadata.
4. Rewrites the catalog as deterministic manifests and per-plugin shards.

The generator writes the canonical packaged source tree under
`config-service/src/config_service`, then optionally updates its registry and runs
`generate_runtime_schemas.py`. Runtime schemas are written to the matching canonical
`src/config_service/json-schemas` tree. Keeping a single tree prevents registration in one
location while schema compilation reads a different location.

## Pre-generation backup

Every command-line invocation creates one compressed snapshot before processing its first
version. The ZIP contains every existing file beneath the canonical packaged `config`,
`json-definitions`, and `json-schemas` directories. By default it is written as:

```text
config-service/backups/config_service_configuration_<UTC timestamp>.zip
```

Use `--backup-dir` to place snapshots elsewhere. The archive is written to a temporary file and
renamed only after compression succeeds. A missing source tree, inaccessible destination,
archive failure, timestamp collision, or destination nested inside archived content stops the
command before scraping or changing any catalog. When several `--version` options are supplied,
one snapshot protects the state that existed before the complete invocation.

The default backup directory is ignored by Git. Retention and removal are deliberate maintainer
tasks; the generator does not delete old snapshots.

See [Plugin JSON File Format](./plugin-json-file-format.md) for the definition/schema distinction
and [Catalog Management](./catalog-management.md) for registry and sharding details.

## Known limitations and review priorities

The current one-pass design has these important limitations:

1. There is no editable discovery document between URL discovery and retrieval.
2. GitHub automatic fallback applies to the entire scrape rather than an individual failed page.
3. Markdown parsing supports one simple pipe table under one exact heading.
4. Website parsing depends on GitBook heading and accessibility-role markup.
5. Required-state inference is only authoritative when a `Required` column exists.
6. Enum inference from prose is deliberately narrow and may miss alternative wording.
7. Numeric range limits generally cannot be inferred from prose.
8. Plugin reconciliation occurs before the enrichment name-normalization pass, so renamed pages
   can require manual correlation.
9. A page with a valid-looking but truncated table can report `ok`; field removals in its summary
   are the signal that a maintainer must investigate.
10. Service options, parser options, processors, and router structures are not scraped from the
    same plugin tables and remain separate generation concerns.

Review these summary entries first:

1. `incomplete_pages`
2. `plugin_not_documented`
3. `field_not_documented`
4. Changes to `required`, `data_type`, `default`, `enum_options`, or `validation_rule`
5. Plugin additions whose name resembles a removed plugin

## Correcting an exceptional page

When a report identifies an incomplete or divergent page:

1. Open the report's reference URL.
2. Confirm the page documents the intended native plugin name.
3. Check whether the configuration section uses the expected heading and table columns.
4. If the page belongs to a different GitHub path, rerun with the correct `--github-ref`.
5. If the page is intentionally exceptional, add a focused parser rule and a unit-test fixture.
6. Rerun with an explicit `--previous-version` to make the comparison repeatable.
7. Review both the Markdown summary and generated plugin shard before registering the version.

Do not manually edit a generated runtime schema as the primary correction. Correct the source
catalog generation or its reconciled definition and regenerate the schemas.

## Testing and quality checks

Focused reconciliation tests:

```bash
python -m pytest -q -s config-service/tests/test_fluentbit_catalog_reconciliation.py
```

Focused linting:

```bash
python -m ruff check \
  config-service/src/config_service/fluentbit_catalog_reconciliation.py \
  config-service/tests/test_fluentbit_catalog_reconciliation.py \
  config-service/dev-tools/generate_fluentbit_assets.py
```

For changes to scraper parsing itself, also run:

```bash
python -m pytest -q -s config-service/tests/test_fluentbit_plugin_name_checker.py
```

Broad changes to artifact contracts or shared generation behavior require the repository security
gate described in the project instructions.

## Extending the design for Fluentd

The reconciliation module operates on the common `plugins.inputs`, `plugins.filters`, and
`plugins.outputs` catalog shape rather than HTTP or Fluent Bit parser internals. A future Fluentd
scraper can reuse its comparison and reporting concepts by supplying engine-specific:

1. Version/ref resolution.
2. Page discovery.
3. Page parsing and extraction confidence.
4. Native plugin-name normalization.
5. Nested-section and directive-argument handling.

Before sharing the implementation directly, engine-specific synthetic fields and Fluentd nested
sections should be represented explicitly in the reconciliation contract. This avoids treating
generated metadata as documentation divergence.
