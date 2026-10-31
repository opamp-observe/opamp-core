#!/usr/bin/env python3
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

from __future__ import annotations

import logging

from config_service.agent_validation.adapters.base import RESULT_KEY_MESSAGES, TemplateCommandAdapter

RESULT_KEY_OK = "ok"
LOGGER = logging.getLogger(__name__)


class FluentdValidationAdapter(TemplateCommandAdapter):
    """Fluentd command and output behavior wrapper."""

    def interpret_result(self, result_text: str) -> dict[str, object]:
        LOGGER.info("starting Fluentd result interpretation")
        parsed = super().interpret_result(result_text)
        messages = parsed.get(RESULT_KEY_MESSAGES, [])
        has_error = any("error" in str(message).lower() for message in messages)
        parsed[RESULT_KEY_OK] = not has_error
        if has_error:
            LOGGER.warning(
                "Fluentd validation output contains error lines message_count=%s",
                len(messages),
            )
        elif not messages:
            LOGGER.warning("Fluentd validation output contained no actionable lines")
        else:
            LOGGER.debug(
                "Fluentd validation output completed without detected errors message_count=%s",
                len(messages),
            )
        LOGGER.info(
            "completed Fluentd result interpretation message_count=%s ok=%s",
            len(messages),
            parsed[RESULT_KEY_OK],
        )
        return parsed
