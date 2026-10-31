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

"""OpenAI-compatible AI connection implementation.

This module is intentionally separate from ``ai_connection.py`` because
``ai_connection.py`` defines the provider-agnostic protocol (interface), while
this file contains the concrete HTTP behavior for OpenAI-compatible APIs.
Keeping protocol and implementation separate allows the planner factory to
swap providers without changing planner/business logic.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_VERIFY_MAX_COMPLETION_TOKEN_ATTEMPTS: tuple[int, ...] = (64, 512)


class OpenAICompatibleConnection:
    """AI connection for OpenAI-compatible `/chat/completions` APIs."""

    _cumulative_token_lock = threading.Lock()
    _cumulative_input_tokens_since_startup = 0
    _cumulative_output_tokens_since_startup = 0

    def __init__(
        self,
        *,
        provider: str,
        api_key_env_var: str,
        base_url: str,
        timeout_seconds: int,
        temperature: float = 0.0,
        max_completion_tokens: int | None = 1024,
        verify_max_completion_tokens_attempts: tuple[int, ...] | None = (
            _VERIFY_MAX_COMPLETION_TOKEN_ATTEMPTS
        ),
        verification_prompt: str = "",
    ) -> None:
        """Store provider runtime settings for subsequent request/verify calls."""
        self.provider = provider
        self.api_key_env_var = api_key_env_var
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_completion_tokens = max_completion_tokens
        self.verify_max_completion_tokens_attempts = tuple(
            verify_max_completion_tokens_attempts
            if verify_max_completion_tokens_attempts
            else _VERIFY_MAX_COMPLETION_TOKEN_ATTEMPTS
        )
        self.verification_prompt = verification_prompt

    def has_api_key(self) -> bool:
        """Return whether configured API key env var is currently set."""
        return bool(os.getenv(self.api_key_env_var))

    def _get_api_key(self) -> str:
        """Load required API key from the configured environment variable."""
        api_key = os.getenv(self.api_key_env_var)
        if not api_key:
            raise RuntimeError(
                f"missing required API key environment variable: {self.api_key_env_var}"
            )
        return api_key

    def _headers(self, *, api_key: str) -> dict[str, str]:
        """Build consistent auth and content-type headers for provider requests."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _extract_usage(data: dict[str, Any]) -> dict[str, int | None]:
        """Extract token usage counters with tolerant type coercion."""
        usage = data.get("usage", {}) if isinstance(data, dict) else {}
        prompt_tokens_raw = usage.get("prompt_tokens")
        completion_tokens_raw = usage.get("completion_tokens")
        total_tokens_raw = usage.get("total_tokens")
        try:
            prompt_tokens = (
                int(prompt_tokens_raw) if prompt_tokens_raw is not None else None
            )
        except (TypeError, ValueError):
            prompt_tokens = None
        try:
            completion_tokens = (
                int(completion_tokens_raw) if completion_tokens_raw is not None else None
            )
        except (TypeError, ValueError):
            completion_tokens = None
        try:
            total_tokens = int(total_tokens_raw) if total_tokens_raw is not None else None
        except (TypeError, ValueError):
            total_tokens = None
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def _log_token_usage(
        self,
        *,
        call_type: str,
        model: str,
        usage: dict[str, int | None],
        max_completion_tokens: int | None,
    ) -> None:
        """Emit standardized token-usage logs for cost/diagnostic visibility."""
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        (
            cumulative_input_tokens,
            cumulative_output_tokens,
        ) = self._update_cumulative_tokens_since_startup(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        logger.info(
            "AI token usage call_type=%s provider=%s model=%s input_tokens=%s output_tokens=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s max_completion_tokens=%s cumulative_input_tokens_since_startup=%s cumulative_output_tokens_since_startup=%s",
            call_type,
            self.provider,
            model,
            input_tokens,
            output_tokens,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
            usage.get("total_tokens"),
            max_completion_tokens,
            cumulative_input_tokens,
            cumulative_output_tokens,
        )

    @classmethod
    def _update_cumulative_tokens_since_startup(
        cls,
        *,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> tuple[int, int]:
        """Accumulate process-lifetime input/output token totals.

        Why class-level accumulation:
        a process can create multiple connection instances during startup and
        runtime; counting at class scope tracks overall usage since server start.
        """
        with cls._cumulative_token_lock:
            if isinstance(input_tokens, int) and input_tokens >= 0:
                cls._cumulative_input_tokens_since_startup += input_tokens
            if isinstance(output_tokens, int) and output_tokens >= 0:
                cls._cumulative_output_tokens_since_startup += output_tokens
            return (
                cls._cumulative_input_tokens_since_startup,
                cls._cumulative_output_tokens_since_startup,
            )

    @classmethod
    def get_cumulative_tokens_since_startup(cls) -> dict[str, int]:
        """Return process-lifetime input/output token totals."""
        with cls._cumulative_token_lock:
            input_tokens = cls._cumulative_input_tokens_since_startup
            output_tokens = cls._cumulative_output_tokens_since_startup
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

    @staticmethod
    def _summarize_response_error(response: httpx.Response) -> str:
        """Return concise provider error summary for raised runtime exceptions."""
        response_text = response.text.strip()
        if not response_text:
            return "no response body"
        try:
            payload = response.json()
        except ValueError:
            return response_text[:500]

        if not isinstance(payload, dict):
            return response_text[:500]
        error_payload = payload.get("error")
        if not isinstance(error_payload, dict):
            return response_text[:500]

        message = str(error_payload.get("message", "")).strip() or response_text[:500]
        extras: list[str] = []
        error_type = error_payload.get("type")
        if error_type:
            extras.append(f"type={error_type}")
        error_code = error_payload.get("code")
        if error_code:
            extras.append(f"code={error_code}")
        error_param = error_payload.get("param")
        if error_param:
            extras.append(f"param={error_param}")
        if extras:
            return f"{message} ({', '.join(extras)})"[:500]
        return message[:500]

    def _verification_metadata(
        self,
        *,
        model: str,
        verification_attempt_count: int,
    ) -> dict[str, Any]:
        """Build common metadata payload used by all verification outcomes."""
        return {
            "provider": self.provider,
            "model": model,
            "base_url": self.base_url,
            "max_completion_tokens": self.max_completion_tokens,
            "verify_max_completion_tokens_attempts": list(
                self.verify_max_completion_tokens_attempts
            ),
            "verification_attempt_count": verification_attempt_count,
        }

    def _verification_failure(
        self,
        *,
        model: str,
        error: str,
        verification_attempt_count: int,
    ) -> dict[str, Any]:
        """Build a consistent non-ok verification payload with context metadata."""
        result = self._verification_metadata(
            model=model,
            verification_attempt_count=verification_attempt_count,
        )
        result.update({"ok": False, "error": error})
        return result

    async def request_json_schema_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        schema_name: str,
        schema: dict[str, Any],
        temperature: float | None = None,
        max_completion_tokens: int | None = None,
    ) -> str:
        """Request a JSON-schema constrained completion and return text content.

        Why this method enforces schema mode:
        planner responses must stay machine-parseable for downstream execution.
        """
        api_key = self._get_api_key()
        effective_temperature = (
            temperature if temperature is not None else self.temperature
        )
        effective_max_completion_tokens = (
            max_completion_tokens
            if max_completion_tokens is not None
            else self.max_completion_tokens
        )
        payload = {
            "model": model,
            "messages": messages,
            "temperature": effective_temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    # strict=True ensures model output stays schema-bound. OpenAI will
                    # reject invalid schemas at request time with HTTP 400.
                    "strict": True,
                },
            },
        }
        if effective_max_completion_tokens is not None:
            payload["max_completion_tokens"] = effective_max_completion_tokens

        logger.debug(
            "Sending planner request provider=%s model=%s base_url=%s",
            self.provider,
            model,
            self.base_url,
        )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(api_key=api_key),
                    json=payload,
                )
            except httpx.RequestError as exc:
                raise RuntimeError(
                    "AI service request failed for planner request: "
                    f"provider={self.provider} base_url={self.base_url} error={exc}"
                ) from exc

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                error_summary = self._summarize_response_error(exc.response)
                raise RuntimeError(
                    "AI service returned "
                    f"{exc.response.status_code} for planner request: {error_summary}"
                ) from exc

            try:
                data = response.json()
            except ValueError as exc:
                response_preview = response.text.strip()[:500] or "no response body"
                raise RuntimeError(
                    "AI service returned non-JSON response for planner request: "
                    f"{response_preview}"
                ) from exc
        usage = self._extract_usage(data)
        self._log_token_usage(
            call_type="planner",
            model=model,
            usage=usage,
            max_completion_tokens=effective_max_completion_tokens,
        )

        raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        if isinstance(raw_content, str):
            return raw_content
        if isinstance(raw_content, list):
            chunks = [
                str(item.get("text", "")) if isinstance(item, dict) else str(item)
                for item in raw_content
            ]
            return "".join(chunks)
        return json.dumps(raw_content, ensure_ascii=False)

    async def verify_connection(self, *, model: str) -> dict[str, Any]:
        """Verify provider reachability and auth using a minimal call.

        Why verification retries token caps:
        some providers return output-limit errors for very small budgets, so we
        retry with configured fallback limits before reporting failure.
        """
        api_key = os.getenv(self.api_key_env_var)
        if not api_key:
            return self._verification_failure(
                model=model,
                error=(
                    "missing required API key environment variable: "
                    f"{self.api_key_env_var}"
                ),
                verification_attempt_count=0,
            )
        verification_prompt = str(self.verification_prompt).strip()
        if not verification_prompt:
            return self._verification_failure(
                model=model,
                error=(
                    "missing required non-empty verification_prompt in planner prompts config"
                ),
                verification_attempt_count=0,
            )

        verification_attempt_count = 0
        used_max_completion_tokens = self.verify_max_completion_tokens_attempts[0]
        usage: dict[str, Any] = {}
        for attempt_index, max_completion_tokens in enumerate(
            self.verify_max_completion_tokens_attempts
        ):
            verification_attempt_count = attempt_index + 1
            used_max_completion_tokens = max_completion_tokens
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": verification_prompt}],
                "max_completion_tokens": max_completion_tokens,
                "temperature": self.temperature,
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(api_key=api_key),
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    usage = self._extract_usage(data)
                    self._log_token_usage(
                        call_type=f"verify.attempt.{verification_attempt_count}",
                        model=model,
                        usage=usage,
                        max_completion_tokens=max_completion_tokens,
                    )
                    break
            except httpx.HTTPStatusError as exc:
                response_text = exc.response.text.strip()
                is_last_attempt = (
                    attempt_index == len(self.verify_max_completion_tokens_attempts) - 1
                )
                if (
                    not is_last_attempt
                    and exc.response.status_code == 400
                    and "model output limit was reached" in response_text.lower()
                ):
                    continue
                return self._verification_failure(
                    model=model,
                    error=(
                        f"AI service returned {exc.response.status_code}: "
                        f"{response_text[:500] or 'no response body'}"
                    ),
                    verification_attempt_count=verification_attempt_count,
                )
            except httpx.RequestError as exc:
                return self._verification_failure(
                    model=model,
                    error=f"AI service request failed: {exc}",
                    verification_attempt_count=verification_attempt_count,
                )
            except Exception as exc:  # pragma: no cover - defensive fallback.
                return self._verification_failure(
                    model=model,
                    error=f"unexpected AI service verification error: {exc}",
                    verification_attempt_count=verification_attempt_count,
                )

        result = self._verification_metadata(
            model=model,
            verification_attempt_count=verification_attempt_count,
        )
        result.update(
            {
                "ok": True,
                "message": "AI service connection verified successfully.",
                "temperature": self.temperature,
                "verification_max_completion_tokens_used": used_max_completion_tokens,
                "usage": usage,
            }
        )
        return result
