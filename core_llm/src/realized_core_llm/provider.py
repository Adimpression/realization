"""Reusable OpenAI-compatible JSON provider for conversation advisors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
import time
from typing import Any

from realized_core_llm.planning import (
    AdvisoryJsonResult,
    ConversationPlanner,
    ConversationRenderer,
    JsonConversationPlanner,
    JsonConversationRenderer,
)


class ConversationProviderConfigurationError(RuntimeError):
    """The selected provider cannot be constructed from explicit settings."""


class ConversationProviderResponseError(RuntimeError):
    """A provider response does not contain one valid JSON object."""


@dataclass(frozen=True, slots=True)
class OpenAICompatibleJsonProvider:
    """Call an injected OpenAI-compatible client and preserve provenance."""

    client: Any
    provider: str
    model: str
    max_tokens: int = 2048
    reasoning_effort: str = "minimal"
    temperature: float | None = 0.0

    def __call__(
        self,
        prompt: str,
        schema: dict[str, Any],
    ) -> AdvisoryJsonResult:
        request_payload = {
            "provider": self.provider,
            "model": self.model,
            "prompt": str(prompt),
            "schema": dict(schema),
            "max_tokens": self.max_tokens,
            "reasoning_effort": self.reasoning_effort,
            "temperature": self.temperature,
        }
        messages = [
            {
                "role": "developer",
                "content": (
                    "Perform the task in the instructions and context, then "
                    "return its actual result as exactly one JSON object that "
                    "satisfies the supplied JSON Schema. The schema and its "
                    "field descriptions are a validation and semantic "
                    "contract, never answer content. Populate every required "
                    "field from the task, leave only genuinely inapplicable "
                    "arrays empty, and add no markdown or commentary."
                    "\n\nApplication-owned instructions and bounded context:\n"
                    + str(prompt)
                ),
            },
            {
                "role": "user",
                "content": (
                    "Required output JSON Schema:\n"
                    + json.dumps(schema, indent=2, sort_keys=True)
                    + "\n\nPerform the task now and return a populated "
                    "instance of this schema."
                ),
            },
        ]
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "response_format": _json_schema_response_format(schema),
        }
        if self.temperature is not None:
            request_kwargs["temperature"] = self.temperature
        if self.provider == "openai" and self.reasoning_effort:
            request_kwargs["reasoning_effort"] = self.reasoning_effort

        started = time.perf_counter()
        response = _create_completion(self.client, request_kwargs)
        elapsed_seconds = round(time.perf_counter() - started, 6)
        raw_text = _response_text(response)
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ConversationProviderResponseError(
                "The conversation provider returned invalid JSON."
            ) from exc
        if not isinstance(payload, Mapping):
            raise ConversationProviderResponseError(
                "The conversation provider must return one JSON object."
            )
        receipt = {
            "source": "llm",
            "provider": self.provider,
            "model": str(getattr(response, "model", None) or self.model),
            "response_id": str(getattr(response, "id", None) or ""),
            "system_fingerprint": str(
                getattr(response, "system_fingerprint", None) or ""
            ),
            "request_digest": _digest(request_payload),
            "response_digest": _digest(
                {"raw_text": raw_text, "payload": dict(payload)}
            ),
            "elapsed_seconds": elapsed_seconds,
        }
        return AdvisoryJsonResult(
            payload={str(key): value for key, value in payload.items()},
            receipt=receipt,
        )


def build_environment_conversation_advisors(
    *,
    provider: str | None = None,
    model: str | None = None,
    client: Any | None = None,
    timeout_seconds: float | None = None,
    reasoning_effort: str | None = None,
) -> tuple[ConversationPlanner, ConversationRenderer]:
    """Build product planner and renderer adapters from explicit/env config."""

    selected_provider = str(
        provider or os.getenv("LLM_PROVIDER", "openai")
    ).strip().casefold()
    if selected_provider not in {"openai", "llamacpp"}:
        raise ConversationProviderConfigurationError(
            f"Unsupported LLM_PROVIDER '{selected_provider}'."
        )
    selected_model = str(
        model
        or os.getenv("LLM_FAST_MODEL", "")
        or (
            os.getenv("LLAMACPP_MODEL", "")
            if selected_provider == "llamacpp"
            else os.getenv("OPENAI_MODEL", "")
        )
    ).strip()
    if not selected_model:
        raise ConversationProviderConfigurationError(
            "No conversation model is configured. Set LLM_FAST_MODEL, "
            "OPENAI_MODEL, or LLAMACPP_MODEL."
        )
    selected_client = client or _build_client(
        selected_provider,
        timeout_seconds=timeout_seconds,
    )
    json_provider = OpenAICompatibleJsonProvider(
        client=selected_client,
        provider=selected_provider,
        model=selected_model,
        reasoning_effort=str(
            reasoning_effort
            or os.getenv("LLM_REASONING_EFFORT", "minimal")
        ).strip().casefold(),
    )
    return (
        JsonConversationPlanner(json_provider),
        JsonConversationRenderer(json_provider),
    )


def _build_client(provider: str, *, timeout_seconds: float | None) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ConversationProviderConfigurationError(
            "The 'openai' package is required for conversation providers."
        ) from exc

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ConversationProviderConfigurationError(
                "OPENAI_API_KEY is not configured."
            )
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        default_timeout = 30.0
    else:
        api_key = os.getenv("LLAMACPP_API_KEY", "llama.cpp").strip()
        base_url = os.getenv(
            "LLAMACPP_BASE_URL",
            "http://127.0.0.1:8080",
        ).strip()
        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
        default_timeout = 2.5
    timeout = timeout_seconds
    if timeout is None:
        try:
            timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", default_timeout))
        except ValueError:
            timeout = default_timeout
    arguments: dict[str, Any] = {
        "api_key": api_key,
        "timeout": max(0.5, float(timeout)),
        "max_retries": 0,
    }
    if base_url:
        arguments["base_url"] = base_url
    return OpenAI(**arguments)


def _create_completion(client: Any, request: dict[str, Any]) -> Any:
    arguments = dict(request)
    while True:
        try:
            return client.chat.completions.create(**arguments)
        except Exception as exc:
            message = str(exc).casefold()
            if (
                "max_tokens" in arguments
                and "max_tokens" in message
                and "max_completion_tokens" in message
            ):
                arguments["max_completion_tokens"] = arguments.pop(
                    "max_tokens"
                )
                continue
            removed = False
            for name in ("reasoning_effort", "temperature", "response_format"):
                unsupported_markers = (
                    "unsupported",
                    "unrecognized",
                    "unknown parameter",
                    "not supported",
                )
                invalid_markers = () if name == "response_format" else ("invalid",)
                if name in arguments and name in message and any(
                    marker in message
                    for marker in (*unsupported_markers, *invalid_markers)
                ):
                    arguments.pop(name, None)
                    removed = True
                    break
            if removed:
                continue
            raise


def _json_schema_response_format(schema: Mapping[str, Any]) -> dict[str, Any]:
    title = str(schema.get("title", "realized_advisory_result")).strip()
    name = "".join(
        character if character.isalnum() or character in {"_", "-"} else "_"
        for character in title
    )[:64]
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name or "realized_advisory_result",
            "strict": True,
            "schema": dict(schema),
        },
    }


def _response_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not choices:
        raise ConversationProviderResponseError(
            "The conversation provider returned no choices."
        )
    content = getattr(getattr(choices[0], "message", None), "content", None)
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        text = "\n".join(
            str(
                item.get("text", "")
                if isinstance(item, Mapping)
                else getattr(item, "text", "")
            )
            for item in content
        ).strip()
    else:
        text = ""
    if not text:
        raise ConversationProviderResponseError(
            "The conversation provider returned no text."
        )
    return text


def _digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "ConversationProviderConfigurationError",
    "ConversationProviderResponseError",
    "OpenAICompatibleJsonProvider",
    "build_environment_conversation_advisors",
]
