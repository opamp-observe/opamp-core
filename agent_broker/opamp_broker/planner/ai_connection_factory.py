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

"""Factory for AI connection providers and normalized planner runtime settings."""

from __future__ import annotations

import os
from typing import Any

from opamp_broker.planner.ai_connection import AIConnection
from opamp_broker.planner.constants import (
    DEFAULT_AI_SVC_API_KEY_ENV,
    DEFAULT_AI_SVC_BASE_URL,
    DEFAULT_AI_SVC_PROVIDER,
    DEFAULT_SLACK_FORMAT_SYSTEM_PROMPT,
    SLACK_FORMAT_SYSTEM_PROMPT_KEY,
    SYSTEM_PROMPT_KEY,
    VERIFICATION_PROMPT_KEY,
)
from opamp_broker.planner.openai_compatible_connection import OpenAICompatibleConnection
from opamp_broker.planner.template_ai_connection import TemplateAIConnection

_PROVIDER_ALIASES: dict[str, str] = {
    "openai": "openai",
    "openai-compatible": "openai",
    "openai_compatible": "openai",
    "template": "template",
}

_DEFAULT_MAX_COMPLETION_TOKENS = 1024
_DEFAULT_VERIFY_MAX_COMPLETION_TOKEN_ATTEMPTS: tuple[int, ...] = (64, 512)
_DEFAULT_TEMPERATURE = 0.0
_DEFAULT_REQUEST_TIMEOUT_SECONDS = 30


def _normalize_optional_positive_int(value: Any, default: int | None) -> int | None:
    """Convert a value to a positive int, otherwise fall back to a safe default.

    Why: planner/runtime config comes from JSON and environment overlays, so we
    defensively normalize types and bounds before creating provider clients.
    """
    try:
        if value is None:
            return default
        normalized = int(value)
    except (TypeError, ValueError):
        return default
    if normalized <= 0:
        return default
    return normalized


def _normalize_request_timeout_seconds(
    value: Any,
    default: int = _DEFAULT_REQUEST_TIMEOUT_SECONDS,
) -> int:
    """Return a valid positive timeout in seconds for outbound AI calls."""
    normalized = _normalize_optional_positive_int(value, default)
    if isinstance(normalized, int):
        return normalized
    return default


def _normalize_verify_attempt_tokens(value: Any) -> tuple[int, ...]:
    """Normalize verification token-attempt list, dropping invalid entries."""
    if not isinstance(value, (list, tuple)):
        return _DEFAULT_VERIFY_MAX_COMPLETION_TOKEN_ATTEMPTS
    normalized: list[int] = []
    for token_limit in value:
        try:
            token_limit_value = int(token_limit)
        except (TypeError, ValueError):
            continue
        if token_limit_value > 0:
            normalized.append(token_limit_value)
    if not normalized:
        return _DEFAULT_VERIFY_MAX_COMPLETION_TOKEN_ATTEMPTS
    return tuple(normalized)


def _normalize_temperature(value: Any, default: float = _DEFAULT_TEMPERATURE) -> float:
    """Clamp model temperature to provider-safe bounds [0.0, 2.0]."""
    try:
        if value is None:
            return default
        normalized = float(value)
    except (TypeError, ValueError):
        return default
    if normalized < 0:
        return 0.0
    if normalized > 2:
        return 2.0
    return normalized


def _normalize_provider_name(provider: str | None) -> str:
    """Normalize provider names and aliases to canonical identifiers."""
    raw_provider = str(provider or DEFAULT_AI_SVC_PROVIDER).strip().lower()
    if not raw_provider:
        raw_provider = DEFAULT_AI_SVC_PROVIDER
    return _PROVIDER_ALIASES.get(raw_provider, raw_provider)


def _resolve_prompt_text(prompts_cfg: dict[str, Any], prompt_key: str, default: str = "") -> str:
    """Resolve prompt text from either direct-string or `{text,description}` formats.

    Why: this keeps planner wiring compatible during prompt-schema migrations
    while still preferring centrally managed prompt config files.
    """
    prompt_value = prompts_cfg.get(prompt_key)
    if isinstance(prompt_value, dict):
        return str(prompt_value.get("text", "")).strip() or default
    if isinstance(prompt_value, str):
        return prompt_value.strip() or default
    return default


def _resolve_prompt_description(prompts_cfg: dict[str, Any], prompt_key: str) -> str:
    """Resolve prompt description text when prompt entries use object format."""
    prompt_value = prompts_cfg.get(prompt_key)
    if isinstance(prompt_value, dict):
        return str(prompt_value.get("description", "")).strip()
    return ""


def resolve_ai_runtime_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize planner runtime settings used by planner and startup checks.

    Why this normalization exists:
    config can arrive from files/env overrides with loose typing, but planner
    wiring requires a predictable structure and bounded numeric values.
    """
    planner_cfg = config.get("planner", {}) if isinstance(config, dict) else {}
    model = str(planner_cfg.get("model", "gpt-5.2")).strip() or "gpt-5.2"
    provider = _normalize_provider_name(planner_cfg.get("provider"))
    timeout_seconds = _normalize_request_timeout_seconds(
        planner_cfg.get("request_timeout_seconds")
    )
    api_key_env_var = str(
        planner_cfg.get("api_key_env_var", DEFAULT_AI_SVC_API_KEY_ENV)
    ).strip() or DEFAULT_AI_SVC_API_KEY_ENV
    base_url = (
        str(planner_cfg.get("base_url", DEFAULT_AI_SVC_BASE_URL)).strip()
        or DEFAULT_AI_SVC_BASE_URL
    )
    max_completion_tokens = _normalize_optional_positive_int(
        planner_cfg.get("max_completion_tokens"),
        _DEFAULT_MAX_COMPLETION_TOKENS,
    )
    verify_max_completion_tokens_attempts = _normalize_verify_attempt_tokens(
        planner_cfg.get("verify_max_completion_tokens_attempts")
    )
    temperature = _normalize_temperature(planner_cfg.get("temperature"))
    prompts_cfg = planner_cfg.get("prompts", {}) if isinstance(planner_cfg, dict) else {}
    if not isinstance(prompts_cfg, dict):
        prompts_cfg = {}
    system_prompt = _resolve_prompt_text(prompts_cfg, SYSTEM_PROMPT_KEY)
    verification_prompt = _resolve_prompt_text(prompts_cfg, VERIFICATION_PROMPT_KEY)
    slack_format_system_prompt = _resolve_prompt_text(
        prompts_cfg,
        SLACK_FORMAT_SYSTEM_PROMPT_KEY,
        default=DEFAULT_SLACK_FORMAT_SYSTEM_PROMPT,
    )
    return {
        "llm_enabled": bool(planner_cfg.get("llm_enabled", True)),
        "provider": provider,
        "model": model,
        "timeout_seconds": timeout_seconds,
        "temperature": temperature,
        "api_key_env_var": api_key_env_var,
        "base_url": base_url,
        "max_completion_tokens": max_completion_tokens,
        "verify_max_completion_tokens_attempts": verify_max_completion_tokens_attempts,
        "system_prompt": system_prompt,
        "verification_prompt": verification_prompt,
        "slack_format_system_prompt": slack_format_system_prompt,
        "prompt_descriptions": {
            SYSTEM_PROMPT_KEY: _resolve_prompt_description(prompts_cfg, SYSTEM_PROMPT_KEY),
            VERIFICATION_PROMPT_KEY: _resolve_prompt_description(
                prompts_cfg, VERIFICATION_PROMPT_KEY
            ),
            SLACK_FORMAT_SYSTEM_PROMPT_KEY: _resolve_prompt_description(
                prompts_cfg, SLACK_FORMAT_SYSTEM_PROMPT_KEY
            ),
        },
        "prompts_config_path": str(planner_cfg.get("prompts_config_path", "")).strip(),
        "api_key_present": bool(os.getenv(api_key_env_var)),
    }


def create_ai_connection(
    *,
    provider: str,
    api_key_env_var: str,
    base_url: str,
    timeout_seconds: int,
    temperature: float = _DEFAULT_TEMPERATURE,
    max_completion_tokens: int | None = _DEFAULT_MAX_COMPLETION_TOKENS,
    verify_max_completion_tokens_attempts: tuple[int, ...] | None = (
        _DEFAULT_VERIFY_MAX_COMPLETION_TOKEN_ATTEMPTS
    ),
    verification_prompt: str = "",
) -> AIConnection:
    """Create the configured AI connection provider instance.

    Why this factory exists:
    planner construction should select provider implementations centrally so
    fail-safe fallback behavior stays consistent across broker startup paths.
    """
    normalized_provider = _normalize_provider_name(provider)
    if normalized_provider == "openai":
        return OpenAICompatibleConnection(
            provider=normalized_provider,
            api_key_env_var=api_key_env_var,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            verify_max_completion_tokens_attempts=verify_max_completion_tokens_attempts,
            verification_prompt=verification_prompt,
        )
    if normalized_provider == "template":
        return TemplateAIConnection(
            provider=normalized_provider,
            api_key_env_var=api_key_env_var,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            verify_max_completion_tokens_attempts=verify_max_completion_tokens_attempts,
            verification_prompt=verification_prompt,
        )
    supported_values = sorted(_PROVIDER_ALIASES.keys())
    raise ValueError(
        f"unsupported AI provider '{provider}'. "
        f"Supported values: {', '.join(supported_values)}"
    )
