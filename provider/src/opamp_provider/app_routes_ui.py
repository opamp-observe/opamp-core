# Copyright 2026 opamp.info
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""UI and static asset route registration for provider app."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from quart import Quart, Response, jsonify, redirect

from opamp_provider.commands import get_available_command_keys

VERSION_KEY = "version"
PLUGINS_KEY = "plugins"
PLUGIN_NAME_KEY = "name"
PLUGIN_AVAILABLE_KEY = "available"
PLUGIN_DESCRIPTION_KEY = "description"
CUSTOM_COMMANDS_NAME = "Custom Commands"
CONFIG_EDITOR_NAME = "Config Editor"
CLIENT_CONFIG_GENERATOR_NAME = "Client Config Generator"
CONFIG_CATALOG_NAME = "Config Catalog"
CONFIG_EDITOR_ENTRY_POINT = "config_service.opamp_integration:register_config_service_feature"
CLIENT_CONFIG_GENERATOR_ENTRY_POINT = (
    "client_config_generator_service.opamp_integration:register_client_config_generator_feature"
)
CONFIG_CATALOG_ENTRY_POINT = "catalog_service.opamp_integration:register_catalog_feature"


def build_provider_version_summary(
    *,
    version: str,
    registered_entry_points: list[str],
    custom_command_count: int,
) -> dict[str, object]:
    """Build a path-free description of the running provider's plugins.

    Parameters
    ----------
    version:
        Packaged provider version shown to operators.
    registered_entry_points:
        Component entry points successfully registered by this process.
    custom_command_count:
        Number of discoverable non-standard commands.
    """
    registered = set(registered_entry_points)
    plugin_descriptions = (
        (CUSTOM_COMMANDS_NAME, custom_command_count > 0,
         f"{custom_command_count} custom command(s) available for connected clients."),
        (CONFIG_EDITOR_NAME, CONFIG_EDITOR_ENTRY_POINT in registered,
         "Edit client configuration in the provider UI."),
        (CLIENT_CONFIG_GENERATOR_NAME, CLIENT_CONFIG_GENERATOR_ENTRY_POINT in registered,
         "Generate client configuration from the provider UI."),
        (CONFIG_CATALOG_NAME, CONFIG_CATALOG_ENTRY_POINT in registered,
         "Browse and select configuration from the provider UI."),
    )
    return {
        VERSION_KEY: version,
        PLUGINS_KEY: [
            {
                PLUGIN_NAME_KEY: name,
                PLUGIN_AVAILABLE_KEY: available,
                PLUGIN_DESCRIPTION_KEY: description,
            }
            for name, available, description in plugin_descriptions
        ],
    }


def register_ui_routes(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-locals
    app: Quart,
    *,
    ui_assets: Any,
    provider_config: Any,
    global_settings_help: dict[str, dict[str, str]],
    render_help_html: Callable[..., str],
    component_version_text: Callable[[], str],
    ui_feature_menu_items: list[Any],
    registered_component_entry_points: list[Any],
) -> None:
    """Register provider UI, help, and static asset routes."""

    @app.get("/")
    async def root() -> Response:
        return redirect("/ui") # pyright: ignore[reportReturnType]

    @app.get("/ui")
    async def web_ui() -> Response:
        """Serve the provider web UI."""
        return Response(ui_assets.web_ui_html, content_type="text/html; charset=utf-8")

    @app.get("/web_ui.css")
    async def web_ui_css() -> Response:
        """Serve the provider web UI stylesheet."""
        return Response(
            ui_assets.web_ui_css,
            content_type="text/css; charset=utf-8",
        )

    @app.get("/web_ui_state.js")
    async def web_ui_state_js() -> Response:
        """Serve the provider web UI state/bootstrap JavaScript."""
        return Response(
            ui_assets.web_ui_state_js,
            content_type="application/javascript; charset=utf-8",
        )

    @app.get("/web_ui_functions.js")
    async def web_ui_functions_js() -> Response:
        """Serve the provider web UI function library JavaScript."""
        return Response(
            ui_assets.web_ui_functions_js,
            content_type="application/javascript; charset=utf-8",
        )

    @app.get("/web_ui_framework.js")
    async def web_ui_framework_js() -> Response:
        """Serve the provider web UI framework/bootstrap JavaScript."""
        return Response(
            ui_assets.web_ui_framework_js,
            content_type="application/javascript; charset=utf-8",
        )

    @app.get("/web_ui_bindings.js")
    async def web_ui_bindings_js() -> Response:
        """Serve the provider web UI event-binding JavaScript."""
        return Response(
            ui_assets.web_ui_bindings_js,
            content_type="application/javascript; charset=utf-8",
        )

    @app.get("/help")
    async def help_page() -> Response:
        """Serve a simple help page."""
        html = render_help_html(
            template_html=ui_assets.help_html,
            global_settings_help=global_settings_help,
            delayed_comms_seconds=provider_config.CONFIG.delayed_comms_seconds,
            significant_comms_seconds=provider_config.CONFIG.significant_comms_seconds,
            component_version=component_version_text(),
        )
        return Response(html, content_type="text/html; charset=utf-8")

    @app.get("/help.css")
    async def help_css() -> Response:
        """Serve the provider help-page stylesheet."""
        return Response(ui_assets.help_css, content_type="text/css; charset=utf-8")

    @app.get("/help.js")
    async def help_js() -> Response:
        """Serve the provider help-page behavior JavaScript."""
        return Response(
            ui_assets.help_js,
            content_type="application/javascript; charset=utf-8",
        )

    @app.get("/doc-set")
    async def latest_docs_redirect() -> Response:
        """Redirect to the latest documentation set."""
        return redirect(provider_config.CONFIG.latest_docs_url)

    @app.get("/api/help/global-settings")
    async def global_settings_help_route() -> Response:
        """Return shared help text used by global settings tooltips and help page."""
        tooltips = {
            key: value.get("tooltip", "") for key, value in global_settings_help.items()
        }
        return jsonify({"fields": global_settings_help, "tooltips": tooltips})

    @app.get("/api/ui/features")
    async def ui_features() -> Response:
        """Return provider UI feature menu entries derived from runtime configuration."""
        items = [
            {
                "entry_point": item.entry_point,
                "label": item.label,
                "url": item.url,
                "target": item.target,
            }
            for item in ui_feature_menu_items
            if str(item.label).strip() and str(item.url).strip()
        ]
        return jsonify(
            {
                "items": items,
                "component_entry_points_registered": registered_component_entry_points,
            }
        )

    @app.get("/api/ui/version")
    async def ui_version() -> Response:
        """Return the provider version and registered plugin availability without paths."""
        command_keys = get_available_command_keys(includedisplayname=False)
        summary = build_provider_version_summary(
            version=component_version_text(),
            registered_entry_points=registered_component_entry_points,
            custom_command_count=len(command_keys),
        )
        return jsonify(summary)

    @app.get("/create.ico")
    async def favicon() -> Response:
        """Serve the UI favicon."""
        return Response(
            ui_assets.icon_path.read_bytes(),
            content_type="image/x-icon",
        )
