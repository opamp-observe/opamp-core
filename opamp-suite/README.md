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

# OpAMP Suite Installation Profiles

`opamp-suite` is a metadata package that provides consistent installation
profiles while keeping every runtime component as an independently versioned
wheel.

```bash
python -m pip install "opamp-suite[server]"
python -m pip install "opamp-suite[editors]"
python -m pip install "opamp-suite[config-editor]"
python -m pip install "opamp-suite[catalog]"
python -m pip install "opamp-suite[client-config-editor]"
python -m pip install "opamp-suite[credentials-editor]"
python -m pip install "opamp-suite[consumer]"
python -m pip install "opamp-suite[all]"
```

- `server` installs the provider and every supported provider plugin service.
- `editors` installs the services that can run as freestanding authoring and
  catalog applications, without the provider.
- `config-editor`, `catalog`, `client-config-editor`, and `credentials-editor`
  install one freestanding service at a time.
- `consumer` installs only the OpAMP consumer framework.
- `all` installs the complete server and consumer profiles.

For local development, `uv` resolves each profile dependency from its adjacent
repository directory through `tool.uv.sources`.
