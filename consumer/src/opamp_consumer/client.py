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

"""Unified consumer entrypoint that routes to the correct runtime implementation.

This module exists so operators can launch one stable command
(`python -m opamp_consumer.client`) without needing to know which concrete
client module to invoke. It parses shared CLI/config options once, resolves
`consumer.service_type`, then dispatches to one of:

- `opamp_consumer.fluentbit.client`
- `opamp_consumer.fluentd.client`
- `opamp_consumer.elastic_agent.client`
- `opamp_consumer.elastic_heartbeat.client`
- `opamp_consumer.simulator.client`

In short: this file is a lightweight router, not a full client implementation.
"""

from __future__ import annotations

import argparse
import sys

from opamp_consumer import config as consumer_config
from opamp_consumer.client_bootstrap import (
    build_common_cli_parser,
    configure_logging_for_config,
    load_config_from_cli_args,
    maybe_print_cli_config,
)
from opamp_consumer.plugin_loader import load_consumer_plugin


def _parse_args_for_routing() -> argparse.Namespace:
    """Parse shared CLI args once to determine target service implementation."""
    parser = build_common_cli_parser()
    args, _unknown = parser.parse_known_args()
    return args


def main() -> None:
    """Route to the concrete consumer entrypoint selected by `consumer.service_type`."""
    args = _parse_args_for_routing()
    if maybe_print_cli_config(args=args):
        return
    config = load_config_from_cli_args(args)
    consumer_config.set_config(config)
    configure_logging_for_config(config)

    target = load_consumer_plugin(config)
    target_module = sys.modules.get(getattr(target, "__module__", ""))
    if target_module is not None and hasattr(target_module, "CONFIG"):
        setattr(target_module, "CONFIG", config)
    target()


if __name__ == "__main__":
    main()
