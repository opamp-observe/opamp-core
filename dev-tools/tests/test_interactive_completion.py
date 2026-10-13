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

"""Tests for guided developer CLI completion backends."""

from __future__ import annotations

import builtins
from types import SimpleNamespace

from opamp_dev_tools import interactive_completion


def test_completion_matches_normalizes_options_and_prefixes() -> None:
    """Matches should be unique, ordered, non-empty, and case-insensitive."""
    matches = interactive_completion.completion_matches(
        "FLU",
        ["fluent-resources", "", "FLUENT-RESOURCES", "build"],
    )

    assert matches == ["fluent-resources"]


def test_prompt_without_interactive_terminal_uses_standard_input(monkeypatch) -> None:
    """Non-terminal execution should preserve ordinary input behavior for tests and pipes."""
    monkeypatch.setattr(interactive_completion, "_interactive_terminal", lambda: False)
    monkeypatch.setattr("builtins.input", lambda prompt_text: f"value:{prompt_text}")

    response = interactive_completion.prompt_with_completion("Choose: ", ["value"])

    assert response == "value:Choose: "


def test_prompt_toolkit_reader_completes_full_selection_labels(monkeypatch) -> None:
    """Prompt-toolkit completion should replace the full current selection prefix."""
    captured: dict[str, object] = {}

    def completion_factory(text: str, *, start_position: int) -> SimpleNamespace:
        """Return a lightweight prompt-toolkit completion record."""
        return SimpleNamespace(text=text, start_position=start_position)

    def prompt_function(
        prompt_text: str,
        *,
        completer: object,
        complete_while_typing: bool,
    ) -> str:
        """Capture prompt configuration and exercise its completer."""
        captured["prompt_text"] = prompt_text
        captured["complete_while_typing"] = complete_while_typing
        captured["matches"] = list(
            completer.get_completions(  # type: ignore[attr-defined]
                SimpleNamespace(text_before_cursor="flu"),
                None,
            )
        )
        return "fluent-resources"

    def import_module(module_name: str) -> SimpleNamespace:
        """Provide prompt-toolkit doubles and reject unrelated imports."""
        if module_name == "prompt_toolkit":
            return SimpleNamespace(prompt=prompt_function)
        if module_name == "prompt_toolkit.completion":
            return SimpleNamespace(Completer=object, Completion=completion_factory)
        raise ImportError(module_name)

    monkeypatch.setattr(interactive_completion, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(interactive_completion.importlib, "import_module", import_module)

    response = interactive_completion.prompt_with_completion(
        "Select: ",
        ["dev", "fluent-resources"],
    )

    assert response == "fluent-resources"
    assert captured["prompt_text"] == "Select: "
    assert captured["complete_while_typing"] is True
    matches = captured["matches"]
    assert isinstance(matches, list)
    assert [(match.text, match.start_position) for match in matches] == [("fluent-resources", -3)]


def test_readline_reader_completes_and_restores_previous_completer(monkeypatch) -> None:
    """Readline fallback should install completion only for the active input call."""
    captured: dict[str, object] = {}

    def previous_completer(_text: str, _state: int) -> None:
        """Represent a completer installed before the developer CLI prompt."""
        return None

    def set_completer(completer: object) -> None:
        """Record completer installation and restoration calls."""
        captured.setdefault("completers", []).append(completer)  # type: ignore[union-attr]

    readline_module = SimpleNamespace(
        get_completer=lambda: previous_completer,
        get_completer_delims=lambda: " \t",
        set_completer=set_completer,
        set_completer_delims=lambda delimiters: captured.setdefault("delimiters", []).append(  # type: ignore[union-attr]
            delimiters
        ),
        parse_and_bind=lambda binding: captured.setdefault("binding", binding),
    )

    def import_module(module_name: str) -> SimpleNamespace:
        """Make prompt-toolkit unavailable and provide a readline double."""
        if module_name == "prompt_toolkit":
            raise ImportError(module_name)
        if module_name == "readline":
            return readline_module
        raise ImportError(module_name)

    def input_reader(prompt_text: str) -> str:
        """Exercise the installed completer before returning input."""
        captured["prompt_text"] = prompt_text
        completer = captured["completers"][-1]  # type: ignore[index]
        captured["first_match"] = completer("b", 0)
        captured["missing_match"] = completer("b", 1)
        return "build"

    monkeypatch.setattr(interactive_completion, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(interactive_completion.importlib, "import_module", import_module)
    monkeypatch.setattr(builtins, "input", input_reader)

    response = interactive_completion.prompt_with_completion("Select: ", ["build", "dev"])

    assert response == "build"
    assert captured["binding"] == "tab: complete"
    assert captured["first_match"] == "build"
    assert captured["missing_match"] is None
    assert captured["completers"][-1] is previous_completer  # type: ignore[index]
    assert captured["delimiters"] == ["", " \t"]


def test_interactive_prompt_falls_back_when_completion_modules_are_missing(monkeypatch) -> None:
    """An interactive terminal without optional backends should still accept input."""
    monkeypatch.setattr(interactive_completion, "_interactive_terminal", lambda: True)
    monkeypatch.setattr(
        interactive_completion.importlib,
        "import_module",
        lambda module_name: (_ for _ in ()).throw(ImportError(module_name)),
    )
    monkeypatch.setattr(builtins, "input", lambda _prompt_text: "dev")

    assert interactive_completion.prompt_with_completion("Select: ", ["dev"]) == "dev"
