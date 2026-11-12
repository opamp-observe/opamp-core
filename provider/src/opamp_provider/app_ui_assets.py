"""UI asset loading helpers for the provider app."""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass

from opamp_provider.ui_assets import mini_filename
from shared.opamp_config import UTF8_ENCODING

APP_ENABLE_DEV_FEATURES_ENV = "APP_ENABLE_DEV_FEATURES"
_ENV_TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ProviderUiAssets:
    """Loaded provider UI assets and static file paths."""

    web_ui_html: str
    web_ui_css: str
    web_ui_state_js: str
    web_ui_functions_js: str
    web_ui_framework_js: str
    web_ui_bindings_js: str
    help_html: str
    help_css: str
    help_js: str
    icon_path: pathlib.Path


def _app_enable_dev_features_enabled() -> bool:
    """Return whether APP_ENABLE_DEV_FEATURES resolves to an enabled value."""
    raw_value = os.environ.get(APP_ENABLE_DEV_FEATURES_ENV, "")
    normalized = str(raw_value or "").strip().lower()
    return normalized in _ENV_TRUE_VALUES


def _read_ui_js_asset(
    *,
    html_dir: pathlib.Path,
    source_filename: str,
    logger: object,
) -> str:
    """Read one UI JS asset with source/minified selection and fallback logging."""
    source_path = html_dir / source_filename
    mini_path = html_dir / mini_filename(source_filename)
    prefer_dev_assets = _app_enable_dev_features_enabled()
    preferred_path = source_path if prefer_dev_assets else mini_path
    fallback_path = mini_path if prefer_dev_assets else source_path
    preferred_exists = preferred_path.exists()
    fallback_exists = fallback_path.exists()

    if (
        not prefer_dev_assets
        and source_path.exists()
        and mini_path.exists()
        and source_path.stat().st_mtime > mini_path.stat().st_mtime
    ):
        logger.warning(
            (
                "provider ui asset source is newer than minified for %s; "
                "serving source=%s instead of stale minified=%s"
            ),
            source_filename,
            str(source_path),
            str(mini_path),
        )
        return source_path.read_text(encoding=UTF8_ENCODING)

    if preferred_exists:
        logger.info(
            "provider ui asset path=%s minified=%s APP_ENABLE_DEV_FEATURES=%s",
            str(preferred_path),
            str(preferred_path.name.endswith(".mini.js")).lower(),
            str(prefer_dev_assets).lower(),
        )
        return preferred_path.read_text(encoding=UTF8_ENCODING)

    if fallback_exists:
        logger.warning(
            (
                "provider ui asset preference could not be honored for %s; "
                "APP_ENABLE_DEV_FEATURES=%s preferred=%s fallback=%s"
            ),
            source_filename,
            str(prefer_dev_assets).lower(),
            str(preferred_path),
            str(fallback_path),
        )
        logger.info(
            "provider ui asset path=%s minified=%s APP_ENABLE_DEV_FEATURES=%s",
            str(fallback_path),
            str(fallback_path.name.endswith(".mini.js")).lower(),
            str(prefer_dev_assets).lower(),
        )
        return fallback_path.read_text(encoding=UTF8_ENCODING)

    raise FileNotFoundError(
        f"no UI asset found for {source_filename}; "
        f"expected at least one of {source_path} or {mini_path}"
    )


def load_provider_ui_assets(*, logger: object) -> ProviderUiAssets:
    """Load provider UI HTML, CSS, JS, help template, and favicon path."""
    html_dir = pathlib.Path(__file__).with_name("html")
    return ProviderUiAssets(
        web_ui_html=(html_dir / "web_ui.html").read_text(encoding=UTF8_ENCODING),
        web_ui_css=(html_dir / "web_ui.css").read_text(encoding=UTF8_ENCODING),
        web_ui_state_js=_read_ui_js_asset(
            html_dir=html_dir,
            source_filename="web_ui_state.js",
            logger=logger,
        ),
        web_ui_functions_js=_read_ui_js_asset(
            html_dir=html_dir,
            source_filename="web_ui_functions.js",
            logger=logger,
        ),
        web_ui_framework_js=_read_ui_js_asset(
            html_dir=html_dir,
            source_filename="web_ui_framework.js",
            logger=logger,
        ),
        web_ui_bindings_js=_read_ui_js_asset(
            html_dir=html_dir,
            source_filename="web_ui_bindings.js",
            logger=logger,
        ),
        help_html=(html_dir / "help.html").read_text(encoding=UTF8_ENCODING),
        help_css=(html_dir / "help.css").read_text(encoding=UTF8_ENCODING),
        help_js=(html_dir / "help.js").read_text(encoding=UTF8_ENCODING),
        icon_path=html_dir / "create.ico",
    )


def render_help_html(
    *,
    template_html: str,
    global_settings_help: dict[str, dict[str, str]],
    delayed_comms_seconds: int,
    significant_comms_seconds: int,
    component_version: str,
) -> str:
    """Render the provider help page template with runtime values."""
    return (
        template_html.replace("__DELAYED_SECONDS__", str(delayed_comms_seconds))
        .replace("__SIGNIFICANT_SECONDS__", str(significant_comms_seconds))
        .replace(
            "__HELP_DELAYED_COMMS_SECONDS__",
            global_settings_help["delayed_comms_seconds"]["tooltip"],
        )
        .replace(
            "__HELP_SIGNIFICANT_COMMS_SECONDS__",
            global_settings_help["significant_comms_seconds"]["tooltip"],
        )
        .replace(
            "__HELP_MINUTES_KEEP_DISCONNECTED__",
            global_settings_help["minutes_keep_disconnected"]["tooltip"],
        )
        .replace(
            "__HELP_CLIENT_EVENT_HISTORY_SIZE__",
            global_settings_help["client_event_history_size"]["tooltip"],
        )
        .replace(
            "__HELP_HUMAN_IN_LOOP_APPROVAL__",
            global_settings_help["human_in_loop_approval"]["tooltip"],
        )
        .replace(
            "__HELP_STATE_PERSISTENCE_ENABLED__",
            global_settings_help["state_persistence_enabled"]["tooltip"],
        )
        .replace(
            "__HELP_STATE_SAVE_FOLDER__",
            global_settings_help["state_save_folder"]["tooltip"],
        )
        .replace(
            "__HELP_RETENTION_COUNT__",
            global_settings_help["retention_count"]["tooltip"],
        )
        .replace(
            "__HELP_AUTOSAVE_INTERVAL_SECONDS_SINCE_CHANGE__",
            global_settings_help["autosave_interval_seconds_since_change"]["tooltip"],
        )
        .replace(
            "__HELP_DEFAULT_HEARTBEAT_FREQUENCY__",
            global_settings_help["default_heartbeat_frequency"]["tooltip"],
        )
        .replace("__SERVER_COMPONENT_VERSION__", component_version)
    )
