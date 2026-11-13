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

# Shared Utilities Package

`opamp-shared` is the independently built distribution that owns the Python
`shared` import package used by OpAMP runtime components.

Components declare `opamp-shared` as a normal runtime dependency. During local
development, each component uses a `tool.uv.sources` path mapping to this
directory, so edits are immediately available without publishing a development
wheel.

```bash
uv sync --project provider --extra dev
uv run --project provider pytest
```

Release builds must use normal dependency metadata rather than the local source
override:

```bash
uv build --no-sources shared
```

The distribution contains configuration, observability, security-header,
remote-configuration, packaging-warning, and UUID helpers. Component wheels
must not copy or vendor files from this directory; the `opamp-shared`
dependency is the single runtime owner of the `shared` package.
