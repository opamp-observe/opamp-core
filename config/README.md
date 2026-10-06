# OpAMP Configuration Variants

Provider-oriented configuration files in this folder:

- `opamp.json`
  - default development configuration with embedded `config-service` editor UI, embedded Config Catalog, and embedded `client-config-generator-service` UI
- `opamp.provider-with-editor-service.json`
  - provider with embedded `config-service` editor UI
- `opamp.provider-with-editor-and-credentials-service.json`
  - provider with embedded `config-service` editor UI and embedded server credentials manager UI
- `opamp.provider-with-editor-and-catalog-services.json`
  - provider with embedded `config-service` editor UI and embedded `catalog-service` catalog UI
- `opamp.provider-with-client-config-generator-service.json`
  - provider with embedded `client-config-generator-service` generator UI

Use a variant explicitly with:

```bash
opamp-provider --config-path ./config/opamp.provider-with-editor-and-catalog-services.json
```

Or set:

```bash
export OPAMP_CONFIG_PATH=./config/opamp.provider-with-editor-service.json
```
