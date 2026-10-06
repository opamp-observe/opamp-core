# Packaging And Deployment

A plugin can be built into the main `opamp-consumer` package or shipped as a
separate Python package. The separate package route is usually better for a new
agent integration because it avoids changing the base consumer release every
time the plugin changes.

## In-Repo Built-In Plugin

Use this route when the plugin is intended to become part of the base consumer.

Add the package under:

```text
consumer/src/opamp_consumer/my_agent/
```

Then add the built-in mapping to:

```text
consumer/src/opamp_consumer/builtin_consumer_plugins.json
```

Example:

```json
{
  "service_type": "my_agent",
  "entry_point": "opamp_consumer.my_agent.client:main",
  "enabled": true
}
```

Because the consumer wheel includes `src/opamp_consumer`, the new package will
be included in the consumer wheel as long as it lives under that package tree.
The JSON registry file is packaged with the consumer and loaded before external
entry points and runtime config overlays.

## External Plugin Package

Use this route when the plugin should deploy independently.

Minimal structure:

```text
my-consumer-plugin/
  pyproject.toml
  src/
    my_consumer_plugin/
      __init__.py
      client.py
  tests/
```

Minimal `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "my-consumer-plugin"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "opamp-consumer>=0.4.1",
]

[project.entry-points."opamp_consumer.plugins"]
my_agent = "my_consumer_plugin.client:main"

[tool.hatch.build.targets.wheel]
packages = ["src/my_consumer_plugin"]
```

Build the wheel with:

```bash
python -m build --wheel
```

Install the base consumer first, then the plugin:

```bash
python -m pip install --upgrade opamp-consumer
python -m pip install --upgrade ./dist/my_consumer_plugin-0.1.0-py3-none-any.whl
```

The order matters because the plugin imports consumer APIs and registers an
entry point into the consumer's plugin group.

## Runtime Config

If the plugin has an installed entry point, runtime config only needs to select
the service type:

```json
{
  "consumer": {
    "service_type": "my_agent"
  }
}
```

You can still include a config overlay when you want the config file to own the
mapping explicitly:

```json
{
  "consumer": {
    "service_type": "my_agent",
    "plugins": [
      {
        "service_type": "my_agent",
        "entry_point": "my_consumer_plugin.client:main",
        "enabled": true
      }
    ]
  }
}
```

To disable an installed plugin without uninstalling it:

```json
{
  "consumer": {
    "plugins": [
      {
        "service_type": "my_agent",
        "enabled": false
      }
    ]
  }
}
```

## Deployment Container

The deployment test container already understands external plugin packages.
See the [deployment test container docs](../../../../tests/test-containers/opamp-consumer-deployment/README.md).

The key setting is:

```env
CONSUMER_PLUGIN_INSTALLS=/host-assets/dist/my_consumer_plugin-0.1.0-py3-none-any.whl
```

The container installs packages in this order:

1. base `opamp-consumer` wheel
2. external plugin wheels or requirement specs from `CONSUMER_PLUGIN_INSTALLS`
3. entry-point verification
4. config staging
5. `opamp-consumer` launch

That order matches the recommended production deployment pattern.

## Checking Installed Entry Points

After installation, verify the entry point is visible in the same Python
environment that will run `opamp-consumer`:

```bash
python -c "from importlib import metadata; print([ep.name + '=' + ep.value for ep in metadata.entry_points().select(group='opamp_consumer.plugins')])"
```

You should see `my_agent=my_consumer_plugin.client:main` in the output.

If the entry point is missing, check:

- the plugin package was installed into the same environment as the consumer
- the package metadata contains `[project.entry-points."opamp_consumer.plugins"]`
- the wheel was rebuilt after editing `pyproject.toml`
- an active `consumer.plugins` entry has not disabled the same `service_type`

## Versioning And Compatibility

Pin the plugin's minimum `opamp-consumer` version to the first consumer version
that contains the APIs you use. If you use newer helpers such as
`ConsumerPluginConfigContext` or the startup banner, reflect that in the
dependency range.

For production, prefer an explicit compatible range, for example:

```toml
dependencies = [
  "opamp-consumer>=0.4.1,<0.5",
]
```

Use the looser form during local development only when you are intentionally
tracking the current repo.

