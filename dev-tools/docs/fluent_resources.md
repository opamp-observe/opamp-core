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

# Fluent Resource Commands

The core developer CLI owns catalog comparison. Config Service conditionally
adds generation commands through
`config-service/dev-tools/opamp_dev_cli_tools.json`. Run
`opamp-dev-cli help` to confirm which commands are available.

## Generate Fluent Bit assets

When Config Service is present, generate the current stable Fluent Bit release
by omitting `--version`:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets
```

Generate one or more named versions by repeating the option:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets --version 5.1.3
opamp-dev-cli fluent-resources generate-fluentbit-assets \
  --version 5.1.3 \
  --version 5.1.4
```

The Config Service generator resolves documentation, reconciles missing data
against the nearest earlier local version, enriches the catalog, updates the
registry, compiles runtime schemas, and writes JSON and Markdown summaries. A
mandatory ZIP backup is completed before repository configuration changes.

Useful controls include:

- `--source auto|github|website`
- `--github-ref REF`
- `--previous-version VERSION`
- `--no-inherit`
- `--no-register`
- `--no-schemas`
- `--summary-dir PATH`
- `--backup-dir PATH`
- `--timeout SECONDS`

Remove a version with:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets \
  --remove-version 5.1.3
```

If that version is a configured default, supply an existing replacement:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-assets \
  --remove-version 5.1.3 \
  --replacement-default 5.0.4
```

`--version` and `--remove-version` are mutually exclusive.

## Generate Fluent Bit Markdown

Generate schema and plugin-attribute quick references from retained local
artifacts:

```bash
opamp-dev-cli fluent-resources generate-fluentbit-markdown --version 5.1.3
```

Repeat `--version` for multiple versions. Use `--skip-schema-reference` or
`--skip-attribute-reference` to generate only one reference type.

## Report Fluent Bit changes

Compare the newest local catalog to its nearest earlier semantic version:

```bash
opamp-dev-cli fluent-resources report-fluentbit-changes
```

Select both sides explicitly:

```bash
opamp-dev-cli fluent-resources report-fluentbit-changes \
  --current-version 5.0.4 \
  --previous-version 4.2.4
```

`--online` builds the target catalog transiently from upstream documentation.
With no current version, it resolves the current stable GitHub release:

```bash
opamp-dev-cli fluent-resources report-fluentbit-changes --online
```

The report identifies candidate new plugins, attributes added to retained
plugins, and wildcard/concrete representation changes. Online comparison does
not register or persist the retrieved catalog.

For scraper internals, reconciliation rules, output files, and incomplete-page
diagnostics, see the Config Service
[Fluent Bit scraper guide](../../config-service/docs/fluentbit_scraper.md).
