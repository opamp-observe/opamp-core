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

FLB_VER_LABEL = "Fluent Bit v"

FILTER_LINE_PREFIXES = ("*", "|", "___", "\\_", "Celebrating",
                        "* Copyright ", "* Fluent Bit is")

FILTER_LINE_CONTAINS = ("Direct Routes Ahead",)
RESULT_KEY_OK = "ok"
RESULT_KEY_USED_VERSION = "used_version"
ERROR_TOKEN = "[error]"

LOGGER = logging.getLogger(__name__)


class FluentBitValidationAdapter(TemplateCommandAdapter):
    """Fluent Bit command and output behavior wrapper."""

    def interpret_result(self, result_text: str) -> dict[str, object]:
        LOGGER.info("starting Fluent Bit result interpretation")
        parsed = super().interpret_result(result_text)
        messages = parsed.get(RESULT_KEY_MESSAGES, [])
        filtered_messages = []
        try:
            for message in messages:
                text = str(message).lstrip()
                LOGGER.debug("inspecting Fluent Bit output line=%s", text)
                if any(text.startswith(prefix) for prefix in FILTER_LINE_PREFIXES):
                    LOGGER.debug("skipping Fluent Bit banner/prefix line=%s", text)
                    continue
                if any(contained in text for contained in FILTER_LINE_CONTAINS):
                    LOGGER.debug("skipping Fluent Bit banner/contains line=%s", text)
                    continue
                if text.startswith(FLB_VER_LABEL) and (RESULT_KEY_USED_VERSION not in parsed):
                    parsed[RESULT_KEY_USED_VERSION] = text[len(FLB_VER_LABEL):]
                    LOGGER.info(
                        "captured Fluent Bit used version used_version=%s source_line=%s",
                        parsed[RESULT_KEY_USED_VERSION],
                        text,
                    )
                    continue

                filtered_messages.append(str(message))
        except Exception:
            LOGGER.exception("failed while processing Fluent Bit validation output")
            filtered_messages = messages

        parsed[RESULT_KEY_MESSAGES] = filtered_messages
        has_error = any(ERROR_TOKEN in str(message).lower() for message in filtered_messages)
        parsed[RESULT_KEY_OK] = not has_error
        if has_error:
            LOGGER.warning(
                "Fluent Bit validation output contains error lines message_count=%s",
                len(filtered_messages),
            )
        elif not filtered_messages:
            LOGGER.warning("Fluent Bit validation output contained no actionable lines")
        LOGGER.info(
            "completed Fluent Bit result interpretation message_count=%s ok=%s",
            len(filtered_messages),
            parsed[RESULT_KEY_OK],
        )
        LOGGER.debug("Fluent Bit parsed payload=%s", parsed)
        return parsed
