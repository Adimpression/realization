"""Typed, stateless transport for OpenAI-compatible chat providers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import json
import time
from typing import Any, Protocol
import urllib.request as urllib_request


class ChatProviderDependencyError(RuntimeError):
    """The optional SDK required by a provider is not installed."""


class ChatCompletionResponseError(RuntimeError):
    """A provider response cannot be represented by the chat contract."""


@dataclass(frozen=True, slots=True)
class ChatToolCall:
    """One provider-neutral function tool call."""

    call_id: str
    name: str
    arguments: str
    call_type: str = "function"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.call_id,
            "type": self.call_type,
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }


@dataclass(frozen=True, slots=True)
class ChatCompletionResponse:
    """Validated first-choice output and non-semantic provider metadata."""

    text: str
    tool_calls: tuple[ChatToolCall, ...] = ()
    model: str | None = None
    response_id: str | None = None
    system_fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class ChatContentPolicy:
    """Compatibility rules for multipart provider message content."""

    mapping_requires_text_type: bool = True
    include_object_text: bool = True
    strip_string_content: bool = True


@dataclass(frozen=True, slots=True)
class ChatRequestFallback:
    """One mechanical request-parameter fallback triggered by an error."""

    parameter: str
    required_error_markers: tuple[str, ...] = ()
    any_error_markers: tuple[str, ...] = ()
    replacement_parameter: str | None = None

    def apply(self, request: dict[str, Any], error_text: str) -> bool:
        if self.parameter not in request:
            return False
        if any(marker not in error_text for marker in self.required_error_markers):
            return False
        if self.any_error_markers and not any(
            marker in error_text for marker in self.any_error_markers
        ):
            return False
        value = request.pop(self.parameter)
        if self.replacement_parameter is not None:
            request[self.replacement_parameter] = value
        return True


@dataclass(frozen=True, slots=True)
class ChatRetryPolicy:
    """A bounded transient-failure policy independent of compatibility retries."""

    max_transient_retries: int = 0
    max_provider_attempts: int | None = None
    retry_delays_seconds: tuple[float, ...] = ()
    retry_status_codes: frozenset[int] = field(default_factory=frozenset)
    retry_server_errors: bool = False
    retry_error_markers: tuple[str, ...] = ()

    def permits_retry(
        self,
        error: Exception,
        *,
        provider_attempts: int,
        transient_retries: int,
    ) -> bool:
        if transient_retries >= max(0, int(self.max_transient_retries)):
            return False
        if (
            self.max_provider_attempts is not None
            and provider_attempts >= max(1, int(self.max_provider_attempts))
        ):
            return False
        status_code = _provider_status_code(error)
        if status_code in self.retry_status_codes:
            return True
        if self.retry_server_errors and status_code is not None and status_code >= 500:
            return True
        error_text = str(error).casefold()
        return any(marker in error_text for marker in self.retry_error_markers)

    def delay_seconds(self, transient_retry_number: int) -> float:
        if not self.retry_delays_seconds:
            return 0.0
        index = min(
            max(0, int(transient_retry_number) - 1),
            len(self.retry_delays_seconds) - 1,
        )
        return max(0.0, float(self.retry_delays_seconds[index]))


class ChatCompletionTransport(Protocol):
    """Port for one stateless provider request."""

    def complete(self, request: Mapping[str, Any]) -> ChatCompletionResponse:
        """Issue and validate one chat-completion request."""


@dataclass(frozen=True, slots=True)
class OpenAICompatibleChatTransport:
    """Adapt an injected OpenAI-compatible client without carrying app state."""

    client: Any = field(repr=False)
    fallbacks: tuple[ChatRequestFallback, ...] = ()
    retry_policy: ChatRetryPolicy = ChatRetryPolicy()
    content_policy: ChatContentPolicy = ChatContentPolicy()
    sleep: Callable[[float], None] = field(default=time.sleep, repr=False)

    def complete(self, request: Mapping[str, Any]) -> ChatCompletionResponse:
        arguments = dict(request)
        provider_attempts = 0
        transient_retries = 0
        while True:
            provider_attempts += 1
            try:
                response = self.client.chat.completions.create(**arguments)
            except Exception as exc:
                error_text = str(exc).casefold()
                if any(
                    fallback.apply(arguments, error_text)
                    for fallback in self.fallbacks
                ):
                    continue
                if not self.retry_policy.permits_retry(
                    exc,
                    provider_attempts=provider_attempts,
                    transient_retries=transient_retries,
                ):
                    raise
                transient_retries += 1
                self.sleep(self.retry_policy.delay_seconds(transient_retries))
                continue
            # Parsing is deliberately outside the provider retry block. Invalid
            # output is a contract failure, not a transient transport failure.
            return parse_chat_completion_response(
                response,
                content_policy=self.content_policy,
            )


def build_openai_compatible_client(
    *,
    api_key: str | None,
    timeout_seconds: float,
    base_url: str | None = None,
) -> Any:
    """Construct the SDK client used by OpenAI-compatible transports."""

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ChatProviderDependencyError(
            "The 'openai' package is required for OpenAI-compatible providers."
        ) from exc

    arguments: dict[str, Any] = {
        "api_key": api_key,
        "timeout": float(timeout_seconds),
        "max_retries": 0,
    }
    if base_url:
        arguments["base_url"] = base_url
    return OpenAI(**arguments)


def normalize_openai_compatible_base_url(base_url: str | None) -> str | None:
    """Reduce endpoint URLs to their OpenAI-compatible API base."""

    if not base_url:
        return None
    normalized = str(base_url).rstrip("/")
    for suffix in (
        "/chat/completions",
        "/responses",
        "/completions",
        "/embeddings",
    ):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def ensure_openai_v1_base_url(base_url: str | None) -> str | None:
    """Normalize a compatible endpoint and ensure its conventional `/v1` root."""

    normalized = normalize_openai_compatible_base_url(base_url)
    if normalized and not normalized.endswith("/v1"):
        return normalized.rstrip("/") + "/v1"
    return normalized


def discover_openai_compatible_model_id(
    base_url: str | None,
    *,
    open_url: Callable[..., Any] | None = None,
    timeout_seconds: float = 2.0,
) -> str | None:
    """Read the first advertised model identifier from a compatible endpoint."""

    if not base_url:
        return None
    opener = open_url or urllib_request.urlopen
    try:
        with opener(
            str(base_url).rstrip("/") + "/models",
            timeout=float(timeout_seconds),
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, Mapping):
        return None
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, Mapping):
                model_id = str(item.get("id") or "").strip()
                if model_id:
                    return model_id
    models = payload.get("models")
    if isinstance(models, list):
        for item in models:
            if isinstance(item, Mapping):
                model_id = str(item.get("model") or item.get("name") or "").strip()
                if model_id:
                    return model_id
    return None


def parse_chat_completion_response(
    response: Any,
    *,
    content_policy: ChatContentPolicy = ChatContentPolicy(),
) -> ChatCompletionResponse:
    """Validate and normalize the first choice of a provider response."""

    choices = _field(response, "choices")
    if not choices:
        raise ChatCompletionResponseError("The provider returned no choices.")
    try:
        first_choice = choices[0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ChatCompletionResponseError(
            "The provider choices are not indexable."
        ) from exc
    message = _field(first_choice, "message")
    if message is None:
        raise ChatCompletionResponseError(
            "The first provider choice has no message."
        )
    return ChatCompletionResponse(
        text=normalize_chat_message_text(message, policy=content_policy),
        tool_calls=normalize_chat_tool_calls(message),
        model=_optional_text(_field(response, "model")),
        response_id=_optional_text(_field(response, "id")),
        system_fingerprint=_optional_text(
            _field(response, "system_fingerprint")
        ),
    )


def normalize_chat_message_text(
    message: Any,
    *,
    policy: ChatContentPolicy = ChatContentPolicy(),
) -> str:
    """Normalize provider message content according to an explicit policy."""

    content = _field(message, "content")
    if isinstance(content, str):
        return content.strip() if policy.strip_string_content else content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, Mapping):
            if (
                not policy.mapping_requires_text_type
                or item.get("type") == "text"
            ):
                parts.append(str(item.get("text", "")))
            continue
        if policy.include_object_text:
            text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
    return "\n".join(part for part in parts if part).strip()


def normalize_chat_tool_calls(message: Any) -> tuple[ChatToolCall, ...]:
    """Normalize function calls without exposing SDK response classes."""

    raw_tool_calls = _field(message, "tool_calls") or ()
    normalized: list[ChatToolCall] = []
    try:
        iterator = iter(raw_tool_calls)
    except TypeError as exc:
        raise ChatCompletionResponseError(
            "Provider tool calls are not iterable."
        ) from exc
    for item in iterator:
        function = _field(item, "function")
        if function is None:
            raise ChatCompletionResponseError(
                "A provider tool call has no function payload."
            )
        call_id = _required_field(item, "id", "tool-call id")
        name = _required_field(function, "name", "tool-call function name")
        arguments = _field(function, "arguments", "{}")
        normalized.append(
            ChatToolCall(
                call_id=str(call_id),
                call_type=str(_field(item, "type", "function")),
                name=str(name),
                arguments=str(arguments if arguments is not None else "{}"),
            )
        )
    return tuple(normalized)


def _provider_status_code(error: Exception) -> int | None:
    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    response_status = getattr(getattr(error, "response", None), "status_code", None)
    return response_status if isinstance(response_status, int) else None


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _required_field(value: Any, name: str, label: str) -> Any:
    result = _field(value, name)
    if result is None:
        raise ChatCompletionResponseError(f"A provider response lacks {label}.")
    return result


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = [
    "ChatCompletionResponse",
    "ChatCompletionResponseError",
    "ChatCompletionTransport",
    "ChatContentPolicy",
    "ChatProviderDependencyError",
    "ChatRequestFallback",
    "ChatRetryPolicy",
    "ChatToolCall",
    "OpenAICompatibleChatTransport",
    "build_openai_compatible_client",
    "discover_openai_compatible_model_id",
    "ensure_openai_v1_base_url",
    "normalize_chat_message_text",
    "normalize_chat_tool_calls",
    "normalize_openai_compatible_base_url",
    "parse_chat_completion_response",
]
