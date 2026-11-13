"""UI and static asset route registration for provider app."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from quart import Quart, Response, jsonify, redirect


def register_ui_routes(  # noqa: PLR0913
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

    @app.get("/create.ico")
    async def favicon() -> Response:
        """Serve the UI favicon."""
        return Response(
            ui_assets.icon_path.read_bytes(),
            content_type="image/x-icon",
        )
