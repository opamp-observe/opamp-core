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

# Custom Validation Logic

## Validation architecture
Validation runs in layers:
1. Schema/semantic checks (`validation_service`)
2. Rule-engine checks (`rule_engine_service`)

The rule engine is profile-driven:
- A profile selects rulesets.
- A ruleset selects one adapter and parameters.

## Existing extension points
- Adapter interface: `config-service/src/config_service/rule_engine/base.py`
- Adapter registry: `config-service/src/config_service/rule_engine/registry.py`
- Built-in adapters: `config-service/src/config_service/rule_engine/adapters/builtin.py`
- Lua code adapter: `config-service/src/config_service/rule_engine/adapters/lua_code.py`
- Rules configuration: `config-service/src/config_service/config/validation-rules-registry.json`

## Built-in custom validator: Lua code syntax
Inline Lua code fields can be validated through the `luaparser` dependency (`py-lua-parser` project on PyPI).

Current implementation:
1. Catalog field must use `data_type: "code"`.
2. Catalog field must include:
```json
{
  "validation_rule": {
    "kind": "code_syntax",
    "language": "lua",
    "parser": "luaparser"
  }
}
```
3. Validation is executed by ruleset `lua_code_syntax`.
4. Returned errors use the normalized structure:
```json
{
  "code": "lua_syntax_error",
  "path": "$.config.pipeline.filters[0].code",
  "message": "Lua syntax error at line 1, column 12: ...",
  "severity": "error",
  "source": "rules"
}
```

## Built-in custom validator: Fluent Bit SQL processor syntax
Inline Fluent Bit SQL processor queries can be validated through the `lark` parsing framework using a custom grammar that mirrors the processor SQL subset.

Current implementation:
1. Catalog field must use `data_type: "code"`.
2. Catalog field must include:
```json
{
  "validation_rule": {
    "kind": "code_syntax",
    "language": "sql",
    "parser": "lark",
    "dialect": "fluentbit_processor_sql"
  }
}
```
3. Validation is executed by ruleset `sql_code_syntax`.
4. Returned errors use the normalized structure:
```json
{
  "code": "sql_syntax_error",
  "path": "$.config.pipeline.inputs[0].processors.logs[0].query",
  "message": "SQL syntax error at line 1, column 8: ...",
  "severity": "error",
  "source": "rules"
}
```

## Add a custom rule adapter
### 1. Create adapter module
Add a new module under:
- `config-service/src/config_service/rule_engine/adapters/`

Implement class extending `RuleAdapter` and return normalized issues:
```python
{
  "code": "my_rule_code",
  "path": "$.config.pipeline.inputs[0].field_name",
  "message": "Validation message",
  "severity": "error",
  "source": "rules"
}
```

### 2. Register adapter
In `src/config_service/rule_engine/registry.py`, map adapter name to class.

Example adapter name:
- `custom.require_tls_on_forward`

### 3. Add ruleset configuration
Update `validation-rules-registry.json`:
```json
{
  "rulesets": {
    "require_tls_on_forward": {
      "adapter": "custom.require_tls_on_forward",
      "enabled": true,
      "params": {
        "enforce": true
      }
    }
  }
}
```

### 4. Add profile binding
Add ruleset to one or more profiles:
```json
{
  "profiles": {
    "strict": {
      "rulesets": [
        "catalog_required_fields",
        "data_type_enforcement",
        "require_tls_on_forward"
      ]
    }
  }
}
```

### 5. Optional version-specific binding
Use `version_overrides` to append rulesets for specific versions.

## Choosing validation profile at runtime
Request payload for `POST /config-service/api/v1/validate/{version}`:
```json
{
  "config": { "pipeline": { "inputs": [], "filters": [], "outputs": [] } },
  "annotations": {},
  "profile": "strict"
}
```

If `profile` is omitted, backend uses `default_profile` from registry.

## Good practices
1. Keep adapters pure and deterministic.
2. Use `params` for behavior switches, not hardcoded constants.
3. Return path-specific issues for good UI mapping.
4. Use stable `code` values for easy filtering/reporting.
5. Add tests for each new adapter and profile behavior.
