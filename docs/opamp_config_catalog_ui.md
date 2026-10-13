# OpAMP Config Catalog UI

## Overview

The provider can host a **Config Catalog** page that indexes configuration files from configured folders and displays metadata extracted from top comment blocks.

- UI route: `/catalog` (default)
- Help route: `/catalog/help` (default)
- Data route: `/catalog/api/files` (default)

The page is added to the provider feature menu when enabled.

When the catalog is hosted inside the provider, the header also includes:

- `Server Console` to return directly to `/ui`
- `Back` to trigger browser-history navigation when a previous page exists

Those buttons stay hidden in standalone catalog deployments.

## Configuration

Configure in `opamp.json` under top-level `opamp.config_catalog`:

```json
{
  "opamp": {
    "config_catalog": {
      "enabled": true,
      "menu_label": "Config Catalog",
      "route_path": "/catalog",
      "help_path": "/catalog/help",
      "ui_base_css_path": "/config-service/ui/assets/config_ui.css",
      "sources": [
        {
          "folder": "config-service/src/config_service/json-definitions",
          "extensions": [".json", ".yaml", ".yml", ".conf"]
        }
      ]
    }
  }
}
```

### Fields

- `enabled`: enables/disables the feature.
- `menu_label`: label used in provider feature dropdown.
- `route_path`: base UI route.
- `help_path`: route for catalog help content.
- `ui_base_css_path`: CSS path used to align appearance with config-service.
- `sources`: folders and extension filters to scan.

## Header Metadata Format

The catalog parser extracts metadata from top comment lines using:

- `config-service: key=value`

Example:

```text
# config-service: config_type=fluentbit
# config-service: version=5.0.4
# config-service: config_version=release-27
```

All discovered keys become table columns.

## Provider UI Feature Menu Integration

Provider feature dropdown entries are configuration-driven from `component-entry-points.quart` entries that include `label` and `url`.

Example:

```json
{
  "component-entry-points": {
    "quart": [
      {
        "entry_point": "config_service.opamp_integration:register_config_service_feature",
        "label": "Config Editor",
        "url": "/config-service/ui",
        "enabled": true
      }
    ]
  }
}
```

## Help

Catalog help page:

- `/catalog/help`

## Selection Checkbox Direction

The catalog selection checkbox capability remains available as part of normal catalog use rather
than being hidden behind a separate mode toggle.

- The fixed first column shows a checkbox for each catalog row.
- The matching column filter supports `Both`, `Selected`, and `Unselected`.
- Clicking the checkbox updates selection state without changing the existing row-click behavior for
  viewing or opening a configuration file.
- The same checkbox workflow can later support ordered file-selection callbacks when those provider
  integration flows are enabled.
- This direction should not prevent the catalog from running standalone, and it should not create a
  dependency for provider deployments that do not enable the catalog feature.

## Callback Apply Flow

When the catalog is opened with a `selection_callback` query parameter:

- an **Apply** button is shown at the bottom-right of the catalog page
- the selected files are posted back to that callback in the order their checkboxes were chosen
- the callback can normalize the list before returning it to the opening server console window
- on success, the catalog popup closes

The checkbox column is still present when no callback is supplied, so standalone catalog browsing and
selection-based filtering continue to work without any provider dependency.
