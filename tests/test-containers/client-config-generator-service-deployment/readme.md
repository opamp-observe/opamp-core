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

# Client Config Generator Deployment Container

This source-mounted container verifies the server plugin deployment boundary in a clean Python image:

- an enabled `component-entry-points.quart` record registers the plugin, exposes its feature-menu metadata, and makes `/client-config-generator-service/ui` reachable;
- the same record with `enabled: false` produces no feature-menu item and leaves the UI route unavailable.

Run from the repository root:

```bash
docker build -f tests/test-containers/client-config-generator-service-deployment/Dockerfile \
  -t opamp-client-config-generator-deployment:latest \
  tests/test-containers/client-config-generator-service-deployment

docker run --rm \
  -v "$PWD:/workspace/opamp" \
  opamp-client-config-generator-deployment:latest
```
