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

"""Print effective provider and consumer configuration."""

from __future__ import annotations

import importlib
import logging
import pathlib
import sys
from types import ModuleType

LOGGER = logging.getLogger(__name__)

ROOT_PATH = pathlib.Path(__file__).resolve().parents[1]
PROVIDER_DIR_NAME = "provider"
CONSUMER_DIR_NAME = "consumer"
SRC_DIR_NAME = "src"
PROVIDER_CONFIG_MODULE = "opamp_provider.config"
CONSUMER_CONFIG_MODULE = "opamp_consumer.config"
MESSAGE_PROVIDER_UNAVAILABLE = "Provider config: unavailable (import failed)"
MESSAGE_PROVIDER_HEADER = "Provider config:"
MESSAGE_PROVIDER_SERVER_CAPABILITIES = "  server_capabilities_mask: {value}"
MESSAGE_CONSUMER_UNAVAILABLE = "Consumer config: unavailable (import failed)"
MESSAGE_CONSUMER_HEADER = "Consumer config:"
MESSAGE_CONSUMER_SERVER_URL = "  server_url: {value}"
MESSAGE_CONSUMER_AGENT_CONFIG_PATH = "  agent_config_path: {value}"
MESSAGE_CONSUMER_AGENT_CAPABILITIES = "  agent_capabilities_mask: {value}"
LOG_FORMAT = "%(levelname)s %(name)s: %(message)s"

PROVIDER_SRC = ROOT_PATH / PROVIDER_DIR_NAME / SRC_DIR_NAME
CONSUMER_SRC = ROOT_PATH / CONSUMER_DIR_NAME / SRC_DIR_NAME
REQUIRED_IMPORT_PATHS = (ROOT_PATH, PROVIDER_SRC, CONSUMER_SRC)


def _repo_root() -> pathlib.Path:
    """Return the repository root path for the shared utilities package."""
    return ROOT_PATH


def _ensure_repo_on_path() -> None:
    """Ensure the repository and component source folders are available on ``sys.path``."""
    LOGGER.info("ensuring repository paths are available for config imports")
    for path in REQUIRED_IMPORT_PATHS:
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)
            LOGGER.info("inserted import path path=%s", path)
        else:
            LOGGER.debug("import path already present path=%s", path)


def _safe_import_config_module(module_name: str) -> ModuleType | None:
    """Import one configuration module without aborting diagnostic output.

    Parameters
    ----------
    module_name:
        Fully qualified module name to import.

    Returns
    -------
    ModuleType | None
        Imported module, or ``None`` when its import fails.
    """
    LOGGER.info("importing config module module=%s", module_name)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        LOGGER.exception("failed to import config module module=%s", module_name)
        return None
    LOGGER.info("imported config module module=%s", module_name)
    return module


def main() -> None:
    """Print key effective configuration values for provider and consumer."""
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    LOGGER.info("starting shared print_config")
    _ensure_repo_on_path()

    provider_config = _safe_import_config_module(PROVIDER_CONFIG_MODULE)
    consumer_config = _safe_import_config_module(CONSUMER_CONFIG_MODULE)

    if provider_config is None:
        LOGGER.warning("provider config module unavailable")
        print(MESSAGE_PROVIDER_UNAVAILABLE)
    else:
        print(MESSAGE_PROVIDER_HEADER)
        print(
            MESSAGE_PROVIDER_SERVER_CAPABILITIES.format(
                value=provider_config.CONFIG.server_capabilities
            )
        )

    if consumer_config is None:
        LOGGER.warning("consumer config module unavailable")
        print(MESSAGE_CONSUMER_UNAVAILABLE)
    else:
        print(MESSAGE_CONSUMER_HEADER)
        print(MESSAGE_CONSUMER_SERVER_URL.format(value=consumer_config.CONFIG.server_url))
        print(
            MESSAGE_CONSUMER_AGENT_CONFIG_PATH.format(
                value=consumer_config.CONFIG.agent_config_path
            )
        )
        print(
            MESSAGE_CONSUMER_AGENT_CAPABILITIES.format(
                value=consumer_config.CONFIG.agent_capabilities
            )
        )
    LOGGER.info("completed shared print_config")


if __name__ == "__main__":
    main()
