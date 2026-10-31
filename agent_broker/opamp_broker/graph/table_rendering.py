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

"""Helpers for fixed-width table rendering in text responses."""

from __future__ import annotations

from typing import Final

DEFAULT_COLUMN_SEPARATOR: Final[str] = " | "
DEFAULT_HEADER_SEPARATOR: Final[str] = "-+-"
DEFAULT_TRUNCATION_SUFFIX: Final[str] = "..."
DEFAULT_FIRST_COLUMN_MAX_WIDTH: Final[int] = 24
DEFAULT_DATA_COLUMN_MAX_WIDTH: Final[int] = 36


def render_fixed_width_table(
    headers: list[str],
    rows: list[list[str]],
    *,
    first_column_max_width: int = DEFAULT_FIRST_COLUMN_MAX_WIDTH,
    data_column_max_width: int = DEFAULT_DATA_COLUMN_MAX_WIDTH,
    column_separator: str = DEFAULT_COLUMN_SEPARATOR,
    header_separator: str = DEFAULT_HEADER_SEPARATOR,
    truncation_suffix: str = DEFAULT_TRUNCATION_SUFFIX,
) -> str:
    """Render rows into a whitespace padded fixed-width table."""
    if not headers:
        return ""

    column_count = len(headers)
    normalized_headers = [str(header) for header in headers]
    normalized_rows = [
        [str(row[index]) if index < len(row) else "" for index in range(column_count)]
        for row in rows
    ]

    widths: list[int] = []
    for index in range(column_count):
        column_values = [normalized_headers[index]] + [
            row[index] for row in normalized_rows
        ]
        raw_max_width = max(len(value) for value in column_values)
        max_allowed_width = (
            first_column_max_width
            if index == 0
            else data_column_max_width
        )
        widths.append(min(raw_max_width, max_allowed_width))

    header_line = column_separator.join(
        _fit_table_cell(
            normalized_headers[index],
            widths[index],
            truncation_suffix=truncation_suffix,
        )
        for index in range(column_count)
    )
    separator_line = header_separator.join(
        "-" * widths[index] for index in range(column_count)
    )
    body_lines = [
        column_separator.join(
            _fit_table_cell(
                row[index],
                widths[index],
                truncation_suffix=truncation_suffix,
            )
            for index in range(column_count)
        )
        for row in normalized_rows
    ]
    return "\n".join([header_line, separator_line] + body_lines)


def _fit_table_cell(
    value: str,
    width: int,
    *,
    truncation_suffix: str,
) -> str:
    if width <= 0:
        return ""
    text = str(value or "")
    if len(text) > width:
        if width <= len(truncation_suffix):
            return text[:width]
        text = text[: width - len(truncation_suffix)]
        text = text + truncation_suffix
    return text.ljust(width)
