# Copyright 2026 mp3monster.org
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Interactive selection input with prompt-toolkit and readline completion."""

from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Callable, Iterable
from typing import Any

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

InputReader = Callable[[str], str]


def prompt_with_completion(prompt_text: str, options: Iterable[str]) -> str:
    """Read input with case-insensitive completion when the terminal supports it.

    Parameters
    ----------
    prompt_text:
        Text displayed immediately before user input.
    options:
        Complete selection values offered for the current prompt.

    """
    completion_options = _normalized_options(options)
    prompt_toolkit_reader = _prompt_toolkit_reader(completion_options)
    if prompt_toolkit_reader is not None:
        LOGGER.debug("using prompt_toolkit developer CLI completion")
        return prompt_toolkit_reader(prompt_text)
    readline_reader = _readline_reader(completion_options)
    if readline_reader is not None:
        LOGGER.debug("using readline developer CLI completion")
        return readline_reader(prompt_text)
    LOGGER.debug("developer CLI completion unavailable; using standard input")
    return input(prompt_text)


def completion_matches(prefix: str, options: Iterable[str]) -> list[str]:
    """Return deterministic case-insensitive full-value prefix matches.

    Parameters
    ----------
    prefix:
        Current full-line selection text.
    options:
        Candidate selection values.

    """
    normalized_prefix = str(prefix or "").strip().lower()
    return [
        option
        for option in _normalized_options(options)
        if option.lower().startswith(normalized_prefix)
    ]


def _prompt_toolkit_reader(options: tuple[str, ...]) -> InputReader | None:
    """Return a prompt-toolkit reader for an interactive terminal.

    Parameters
    ----------
    options:
        Normalized full-line completion values.

    """
    if not _interactive_terminal():
        return None
    try:
        prompt_function = importlib.import_module("prompt_toolkit").prompt
        completion_module = importlib.import_module("prompt_toolkit.completion")
    except ImportError:
        return None
    completer_base = completion_module.Completer
    completion_type = completion_module.Completion

    class _SelectionCompleter(completer_base):  # pylint: disable=too-few-public-methods
        """Complete full selection labels for the active guided menu.

        Attributes
        ----------
        values:
            Normalized selection values offered by the active prompt.

        """

        def __init__(self, values: tuple[str, ...]) -> None:
            """Store the values offered by the active prompt.

            Parameters
            ----------
            values:
                Normalized full-line completion values.

            """
            self.values = values

        def get_completions(
            self,
            document: Any,
            _complete_event: Any,
        ) -> Iterable[Any]:
            """Yield prefix-matching prompt-toolkit completion records.

            Parameters
            ----------
            document:
                Prompt-toolkit document containing text before the cursor.
            _complete_event:
                Prompt-toolkit completion event, unused for static choices.

            """
            prefix = str(document.text_before_cursor or "")
            for match in completion_matches(prefix, self.values):
                yield completion_type(match, start_position=-len(prefix))

    completer = _SelectionCompleter(options)

    def reader(prompt_text: str) -> str:
        """Read one value through prompt-toolkit completion.

        Parameters
        ----------
        prompt_text:
            Text displayed before the selection input.

        """
        return str(
            prompt_function(
                prompt_text,
                completer=completer,
                complete_while_typing=True,
            )
        )

    return reader


def _readline_reader(options: tuple[str, ...]) -> InputReader | None:
    """Return a readline-backed reader for an interactive terminal.

    Parameters
    ----------
    options:
        Normalized full-line completion values.

    """
    if not _interactive_terminal():
        return None
    try:
        readline_module = importlib.import_module("readline")
    except ImportError:
        return None

    def completer(text: str, state: int) -> str | None:
        """Return one readline completion match by state index.

        Parameters
        ----------
        text:
            Current token supplied by readline.
        state:
            Zero-based requested match index.

        """
        matches = completion_matches(text, options)
        return matches[state] if state < len(matches) else None

    def reader(prompt_text: str) -> str:
        """Read one value while temporarily installing the completer.

        Parameters
        ----------
        prompt_text:
            Text displayed before the selection input.

        """
        previous_completer = readline_module.get_completer()
        previous_delimiters = readline_module.get_completer_delims()
        readline_module.set_completer(completer)
        readline_module.set_completer_delims("")
        readline_module.parse_and_bind("tab: complete")
        try:
            return input(prompt_text)
        finally:
            readline_module.set_completer(previous_completer)
            readline_module.set_completer_delims(previous_delimiters)

    return reader


def _normalized_options(options: Iterable[str]) -> tuple[str, ...]:
    """Return unique non-empty options while preserving display order.

    Parameters
    ----------
    options:
        Candidate completion values in display order.

    """
    normalized: list[str] = []
    seen: set[str] = set()
    for option in options:
        value = str(option).strip()
        normalized_key = value.lower()
        if not value or normalized_key in seen:
            continue
        seen.add(normalized_key)
        normalized.append(value)
    return tuple(normalized)


def _interactive_terminal() -> bool:
    """Return whether standard input and output are attached to a terminal."""
    return bool(sys.stdin.isatty() and sys.stdout.isatty())
