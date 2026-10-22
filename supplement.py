# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request as urllib_request
from collections.abc import Mapping
from typing import Any

from applied_theory_types import (
    LLMSupplementReceipt,
    LLMSupplementResult,
    ProposalType,
    SupplementMode,
    json_safe,
)


def proposal_type_label(proposal_type: ProposalType) -> str:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling proposal type label.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `proposal_type_label(proposal_type=ProposalType.NOT_ELABORATION)`
        Output: 'F = m * a'

    Args:
        proposal_type: Value for `proposal_type` used by `proposal_type_label`. Expected type: `ProposalType`.

    Returns:
        str: Result produced by `proposal_type_label`.
    """
    labels = {
        ProposalType.SEMANTIC_TARGET: "Task Clarification",
        ProposalType.NOT_ELABORATION: "Not Elaboration",
        ProposalType.MARKDOWN_LEARNING: "Markdown Learning",
        ProposalType.MARKDOWN_TITLE_REPAIR: "Markdown Title Repair",
        ProposalType.MARKDOWN_ABILITY_LEARNING: "Markdown Ability Learning",
        ProposalType.MARKDOWN_FUNCTIONALIZATION: "Markdown Functionalization",
        ProposalType.MARKDOWN_EXPRESSION_SYNTHESIS: "Markdown Expression Synthesis",
        ProposalType.DIRECT_RESOLUTION: "Direct Resolution",
        ProposalType.CONTROL_DECISION: "Control Decision",
        ProposalType.NODE_ASSESSMENT: "Node Assessment",
        ProposalType.DISCOVERY_AUDIT: "Discovery Audit",
        ProposalType.IMMEDIATE_LEARNING: "Adjacent Learning",
        ProposalType.CANDIDATE_SELECTION: "Candidate Choice",
        ProposalType.NOT_DECOMPOSITION: "Not Decomposition",
        ProposalType.RETRIEVAL_PLAN: "Research Plan",
        ProposalType.CAPABILITY_DRAFT: "Needed Capability",
        ProposalType.UNCERTAINTY_ASSESSMENT: "Uncertainty Review",
        ProposalType.NEXT_ACTION: "Next Step",
        ProposalType.REALIZATION_WITNESS: "Realization Witness",
        ProposalType.REFLECTION: "Progress Review",
        ProposalType.CONTEMPLATION: "Path Comparison",
        ProposalType.REFRAME: "Problem Reframe",
        ProposalType.EXPLANATION_DRAFT: "Status Explanation",
        ProposalType.DST_DISCOVERY: "DST Discovery",
        ProposalType.DST_NORMALIZATION: "DST Normalization",
    }
    return labels[proposal_type]


def normalize_openai_base_url_for_supplement_client(base_url: str | None) -> str | None:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with normalizing openai base url for supplement client.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `normalize_openai_base_url_for_supplement_client(base_url='force')`
        Output: 'F = m * a'

    Args:
        base_url: Value for `base_url` used by `normalize_openai_base_url_for_supplement_client`. Expected type: `str | None`.

    Returns:
        str | None: Result produced by `normalize_openai_base_url_for_supplement_client`.
    """
    if not base_url:
        return None

    normalized = base_url.rstrip("/")
    for suffix in ("/chat/completions", "/responses", "/completions", "/embeddings"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def resolve_llm_provider_from_environment() -> str:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with resolving llm provider from environment.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `resolve_llm_provider_from_environment()`
        Output: 'F = m * a'

    Args:
        None.

    Returns:
        str: Result produced by `resolve_llm_provider_from_environment`.
    """
    return os.getenv("LLM_PROVIDER", "openai").strip().lower()


def resolve_llm_base_url_for_provider(provider: str) -> str | None:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with resolving llm base url for provider.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `resolve_llm_base_url_for_provider(provider='force')`
        Output: 'F = m * a'

    Args:
        provider: Value for `provider` used by `resolve_llm_base_url_for_provider`. Expected type: `str`.

    Returns:
        str | None: Result produced by `resolve_llm_base_url_for_provider`.
    """
    if provider == "llamacpp":
        normalized = normalize_openai_base_url_for_supplement_client(
            os.getenv("LLAMACPP_BASE_URL", "http://127.0.0.1:8080")
        )
        if normalized and not normalized.endswith("/v1"):
            normalized = normalized.rstrip("/") + "/v1"
        return normalized
    return normalize_openai_base_url_for_supplement_client(os.getenv("OPENAI_BASE_URL"))


def discover_llamacpp_model_id_from_server(base_url: str | None) -> str | None:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling discover llamacpp model id from server.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `discover_llamacpp_model_id_from_server(base_url='force')`
        Output: 'F = m * a'

    Args:
        base_url: Value for `base_url` used by `discover_llamacpp_model_id_from_server`. Expected type: `str | None`.

    Returns:
        str | None: Result produced by `discover_llamacpp_model_id_from_server`.
    """
    if not base_url:
        return None

    models_url = base_url.rstrip("/") + "/models"
    try:
        with urllib_request.urlopen(models_url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
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


def resolve_llm_model_name(provider: str, explicit_model: str | None) -> str:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with resolving llm model name.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `resolve_llm_model_name(provider='force', explicit_model='force')`
        Output: 'F = m * a'

    Args:
        provider: Value for `provider` used by `resolve_llm_model_name`. Expected type: `str`.
        explicit_model: Value for `explicit_model` used by `resolve_llm_model_name`. Expected type: `str | None`.

    Returns:
        str: Result produced by `resolve_llm_model_name`.
    """
    if explicit_model:
        return explicit_model
    if provider == "llamacpp":
        configured = os.getenv("LLAMACPP_MODEL")
        if configured and configured != "local-model":
            return configured
        discovered = discover_llamacpp_model_id_from_server(
            resolve_llm_base_url_for_provider(provider)
        )
        return discovered or configured or os.getenv("OPENAI_MODEL") or "local-model"
    return os.getenv("OPENAI_MODEL", "")


def resolve_llm_client_timeout_seconds(provider: str) -> float:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with resolving llm client timeout seconds.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `resolve_llm_client_timeout_seconds(provider='force')`
        Output: 0.75

    Args:
        provider: Value for `provider` used by `resolve_llm_client_timeout_seconds`. Expected type: `str`.

    Returns:
        float: Result produced by `resolve_llm_client_timeout_seconds`.
    """
    default_timeout = "2.5" if provider == "llamacpp" else "30.0"
    raw_timeout = os.getenv("LLM_TIMEOUT_SECONDS", default_timeout)
    try:
        return max(0.5, float(raw_timeout))
    except ValueError:
        return float(default_timeout)


def build_openai_compatible_llm_client(provider: str) -> Any:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with building openai compatible llm client.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `build_openai_compatible_llm_client(provider='force')`
        Output: 'F = m * a'

    Args:
        provider: Value for `provider` used by `build_openai_compatible_llm_client`. Expected type: `str`.

    Returns:
        Any: Result produced by `build_openai_compatible_llm_client`.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("The 'openai' package is required for LLM supplements.") from exc

    if provider == "llamacpp":
        api_key = os.getenv("LLAMACPP_API_KEY", "llama.cpp")
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set.")
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER '{provider}'.")

    client_kwargs: dict[str, Any] = {
        "api_key": api_key,
        "timeout": resolve_llm_client_timeout_seconds(provider),
        "max_retries": 0,
    }
    base_url = resolve_llm_base_url_for_provider(provider)
    if base_url:
        client_kwargs["base_url"] = base_url

    return OpenAI(**client_kwargs)


def ask_llm(
    prompt: str,
    *,
    model: str | None = None,
    temperature: float | None = 0.0,
    max_tokens: int = 2048,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | None = None,
    system_msg: str | None = None,
    reasoning_effort: str | None = None,
    response_format: dict[str, Any] | None = None,
    seed: int | None = None,
    return_metadata: bool = False,
) -> str | tuple[str, dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling ask llm.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `ask_llm(prompt='Compute force from mass and acceleration.', model='force', temperature=3, max_tokens=3)`
        Output: 'F = m * a'

    Args:
        prompt: Value for `prompt` used by `ask_llm`. Expected type: `str`.
        model: Value for `model` used by `ask_llm`. Expected type: `str | None`. Defaults to `None`.
        temperature: Value for `temperature` used by `ask_llm`. Expected type: `float | None`. Defaults to `0.0`.
        max_tokens: Value for `max_tokens` used by `ask_llm`. Expected type: `int`. Defaults to `2048`.
        tools: Value for `tools` used by `ask_llm`. Expected type: `list[dict[str, Any]] | None`. Defaults to `None`.
        tool_choice: Value for `tool_choice` used by `ask_llm`. Expected type: `str | None`. Defaults to `None`.
        system_msg: Value for `system_msg` used by `ask_llm`. Expected type: `str | None`. Defaults to `None`.
        reasoning_effort: Value for `reasoning_effort` used by `ask_llm`. Expected type: `str | None`. Defaults to `None`.
        response_format: Value for `response_format` used by `ask_llm`. Expected type: `dict[str, Any] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `ask_llm`.
    """
    provider = resolve_llm_provider_from_environment()
    model = resolve_llm_model_name(provider, model)
    if not model:
        raise RuntimeError(
            "No model configured. Set OPENAI_MODEL or LLAMACPP_MODEL for the selected LLM_PROVIDER."
        )

    messages: list[dict[str, Any]] = []
    if system_msg:
        messages.append({"role": "developer", "content": system_msg})
    messages.append({"role": "user", "content": prompt})

    client = build_openai_compatible_llm_client(provider)
    request_kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if tools is not None:
        request_kwargs["tools"] = tools
    if tool_choice is not None:
        request_kwargs["tool_choice"] = tool_choice
    if provider == "openai" and reasoning_effort:
        request_kwargs["reasoning_effort"] = reasoning_effort
    if response_format is not None:
        request_kwargs["response_format"] = response_format
    if temperature is not None:
        request_kwargs["temperature"] = temperature
    if seed is not None:
        request_kwargs["seed"] = seed

    transient_retry_count = 0
    while True:
        try:
            response = client.chat.completions.create(**request_kwargs)
            break
        except Exception as exc:
            error_text = str(exc).lower()
            unsupported_max_tokens = (
                "max_tokens" in request_kwargs
                and "max_tokens" in error_text
                and "max_completion_tokens" in error_text
            )
            if unsupported_max_tokens:
                request_kwargs["max_completion_tokens"] = request_kwargs.pop("max_tokens")
                continue

            unsupported_reasoning_effort = (
                "reasoning_effort" in request_kwargs
                and "reasoning_effort" in error_text
                and any(
                    marker in error_text
                    for marker in (
                        "unsupported",
                        "unrecognized request argument",
                        "unknown parameter",
                        "not supported",
                    )
                )
            )
            if unsupported_reasoning_effort:
                request_kwargs.pop("reasoning_effort", None)
                continue

            unsupported_temperature = (
                "temperature" in request_kwargs
                and "temperature" in error_text
                and ("unsupported" in error_text or "default (1)" in error_text)
            )
            if unsupported_temperature:
                request_kwargs.pop("temperature", None)
                continue

            unsupported_response_format = (
                "response_format" in request_kwargs
                and "response_format" in error_text
                and ("unsupported" in error_text or "invalid" in error_text)
            )
            if unsupported_response_format:
                request_kwargs.pop("response_format", None)
                continue
            unsupported_seed = (
                "seed" in request_kwargs
                and "seed" in error_text
                and ("unsupported" in error_text or "invalid" in error_text)
            )
            if unsupported_seed:
                request_kwargs.pop("seed", None)
                continue
            transient_transport_error = any(
                marker in error_text
                for marker in (
                    "apiconnectionerror",
                    "connection error",
                    "connection reset by peer",
                    "temporarily unavailable",
                    "timed out",
                    "timeout",
                    "remoteprotocolerror",
                )
            )
            if transient_transport_error and transient_retry_count < 2:
                transient_retry_count += 1
                time.sleep(1.0 * transient_retry_count)
                continue
            raise

    content = response.choices[0].message.content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, Mapping) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        text = "\n".join(parts).strip()
    else:
        text = content.strip() if content else ""

    metadata: dict[str, Any] = {}
    system_fingerprint = getattr(response, "system_fingerprint", None)
    if system_fingerprint:
        metadata["system_fingerprint"] = str(system_fingerprint)
    response_model = getattr(response, "model", None)
    if response_model:
        metadata["model"] = str(response_model)
    response_id = getattr(response, "id", None)
    if response_id:
        metadata["response_id"] = str(response_id)

    if return_metadata:
        return text, metadata
    return text


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_digest(payload: Any) -> str:
    canonical = json.dumps(json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _sha256_text(canonical)


def llm_supplement_request_digest(
    *,
    proposal_type: ProposalType,
    mode: SupplementMode,
    prompt: str,
    schema_hint: dict[str, Any],
    max_tokens: int,
    reasoning_effort: str,
    response_format: dict[str, Any],
    temperature: float | None,
    system_msg: str,
    seed: int | None,
) -> str:
    envelope = {
        "proposal_type": proposal_type.value,
        "mode": mode.value,
        "prompt": prompt,
        "schema_hint": schema_hint,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "reasoning_effort": reasoning_effort,
        "response_format": response_format,
        "system_msg": system_msg,
        "seed": seed,
    }
    return _canonical_digest(envelope)


def llm_supplement_system_message() -> str:
    return (
        "Return exactly one JSON object matching the requested shape. "
        "Use plain, concrete language and avoid internal framework names or abstract theory terms."
    )


def extract_json_payload_from_llm_text(text: str) -> Any:
    """
    High Level Purpose:
        In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling extract json payload from llm text.

    Reference to Theory:
        Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

    Example Input Output:
        Input: `extract_json_payload_from_llm_text(text='Compute force from mass and acceleration.')`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        text: Value for `text` used by `extract_json_payload_from_llm_text`. Expected type: `str`.

    Returns:
        Any: Result produced by `extract_json_payload_from_llm_text`.
    """
    candidate = text.strip()
    fenced_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", candidate, re.DOTALL)
    if fenced_match:
        candidate = fenced_match.group(1).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    object_match = re.search(r"(\{.*\}|\[.*\])", candidate, re.DOTALL)
    if not object_match:
        raise RuntimeError("LLM did not return valid JSON.")
    return json.loads(object_match.group(1))


class LLMSupplement:
    def __init__(self, policy: str = "auto") -> None:
        """
        High Level Purpose:
            In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with initializing the surrounding object with a usable starting state.

        Reference to Theory:
            Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

        Example Input Output:
            Input: `__init__(policy='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            policy: Value for `policy` used by `__init__`. Expected type: `str`. Defaults to `'auto'`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.policy = policy.strip().lower()
        self.provider = resolve_llm_provider_from_environment()
        self.base_url = resolve_llm_base_url_for_provider(self.provider)
        self.fast_model = resolve_llm_model_name(self.provider, os.getenv("LLM_FAST_MODEL"))
        self.deep_model = resolve_llm_model_name(self.provider, os.getenv("LLM_DEEP_MODEL"))
        self.enabled = self._compute_enabled()

    def _compute_enabled(self) -> bool:
        """
        High Level Purpose:
            In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling compute enabled.

        Reference to Theory:
            Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

        Example Input Output:
            Input: `_compute_enabled()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `_compute_enabled`.
        """
        if self.policy == "off":
            return False
        if self.provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        if self.provider == "llamacpp":
            return True
        if self.policy == "required":
            raise RuntimeError(f"Unsupported LLM provider '{self.provider}'.")
        return False

    def ensure_available(self) -> None:
        """
        High Level Purpose:
            In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling ensure available.

        Reference to Theory:
            Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

        Example Input Output:
            Input: `ensure_available()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self.policy == "required" and not self.enabled:
            if self.provider == "openai":
                raise RuntimeError(
                    "LLM supplements were required but OPENAI_API_KEY is not configured."
                )
            raise RuntimeError(
                f"LLM supplements were required but provider '{self.provider}' is unavailable."
            )

    def model_for_mode(self, mode: SupplementMode) -> str | None:
        """
        High Level Purpose:
            In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling model for mode.

        Reference to Theory:
            Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

        Example Input Output:
            Input: `model_for_mode(mode=SupplementMode.REQUIRED)`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            mode: Value for `mode` used by `model_for_mode`. Expected type: `SupplementMode`.

        Returns:
            str | None: Result produced by `model_for_mode`.
        """
        if mode == SupplementMode.DEEP:
            return self.deep_model or self.fast_model
        return self.fast_model or self.deep_model

    def max_tokens_for_mode(self, mode: SupplementMode) -> int:
        """
        High Level Purpose:
            In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling max tokens for mode.

        Reference to Theory:
            Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

        Example Input Output:
            Input: `max_tokens_for_mode(mode=SupplementMode.REQUIRED)`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            mode: Value for `mode` used by `max_tokens_for_mode`. Expected type: `SupplementMode`.

        Returns:
            int: Result produced by `max_tokens_for_mode`.
        """
        env_key = (
            "LLM_DEEP_MAX_TOKENS" if mode == SupplementMode.DEEP else "LLM_FAST_MAX_TOKENS"
        )
        default = 4096 if mode == SupplementMode.DEEP else 3072
        raw_value = os.getenv(env_key, str(default)).strip()
        try:
            return max(256, int(raw_value))
        except ValueError:
            return default

    def describe(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with handling describe.

        Reference to Theory:
            Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

        Example Input Output:
            Input: `describe()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `describe`.
        """
        return {
            "policy": self.policy,
            "enabled": self.enabled,
            "provider": self.provider,
            "base_url": self.base_url,
            "fast_model": self.fast_model,
            "deep_model": self.deep_model,
        }

    def propose_json(
        self,
        *,
        proposal_type: ProposalType,
        mode: SupplementMode,
        prompt: str,
        schema_hint: dict[str, Any],
        seed: int | None = None,
    ) -> LLMSupplementResult:
        """
        High Level Purpose:
            In circumstances like LLM-backed proposal generation and supplemental reasoning, helps with proposing json.

        Reference to Theory:
            Provides LLM supplementation utilities used by the controller when theory-driven learning needs model assistance.

        Example Input Output:
            Input: `propose_json(proposal_type=ProposalType.NOT_ELABORATION, mode=SupplementMode.REQUIRED, prompt='Compute force from mass and acceleration.', schema_hint={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: '{"title": "Physics / Force / Force From Mass And Acceleration"}'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal_type: Value for `proposal_type` used by `propose_json`. Expected type: `ProposalType`.
            mode: Value for `mode` used by `propose_json`. Expected type: `SupplementMode`.
            prompt: Value for `prompt` used by `propose_json`. Expected type: `str`.
            schema_hint: Value for `schema_hint` used by `propose_json`. Expected type: `dict[str, Any]`.

        Returns:
            LLMSupplementResult: Result produced by `propose_json`.
        """
        self.ensure_available()
        if not self.enabled:
            return LLMSupplementResult(
                payload=None, source="disabled", provider=self.provider, model=None
            )

        model = self.model_for_mode(mode)
        task_label = proposal_type_label(proposal_type)
        depth_label = "quick pass" if mode == SupplementMode.FAST else "deeper pass"
        system_msg = llm_supplement_system_message()
        user_msg = (
            f"Task: {task_label}\n"
            f"Depth: {depth_label}\n"
            "Return exactly one JSON object matching this schema shape:\n"
            f"{json.dumps(schema_hint, indent=2, sort_keys=True)}\n\n"
            "Instructions and context:\n"
            f"{prompt}\n\n"
            "Rules:\n"
            "- Use the field names exactly as shown in the schema.\n"
            "- Fill every top-level field.\n"
            "- Keep wording specific and practical.\n"
            "- Do not add markdown, commentary, or extra text outside the JSON object."
        )

        reasoning_effort = "minimal" if mode == SupplementMode.FAST else "medium"
        response_format = {"type": "json_object"}
        request_digest = llm_supplement_request_digest(
            proposal_type=proposal_type,
            mode=mode,
            prompt=prompt,
            schema_hint=schema_hint,
            max_tokens=self.max_tokens_for_mode(mode),
            reasoning_effort=reasoning_effort,
            response_format=response_format,
            temperature=0.0,
            system_msg=system_msg,
            seed=seed,
        )

        raw_text = ""
        response_meta: dict[str, Any] = {}
        payload: Any = None
        repair_count = 0
        parse_status = "ok"

        try:
            raw = ask_llm(
                user_msg,
                model=model,
                temperature=0.0,
                max_tokens=self.max_tokens_for_mode(mode),
                system_msg=system_msg,
                reasoning_effort=reasoning_effort,
                response_format=response_format,
                seed=seed,
                return_metadata=True,
            )
            raw_text, response_meta = raw if isinstance(raw, tuple) else (str(raw), {})
            try:
                payload = extract_json_payload_from_llm_text(raw_text)
            except Exception:
                repair_count += 1
                parse_status = "repair"
                repair_msg = (
                    f"{user_msg}\n\n"
                    "Your previous answer was not valid JSON.\n"
                    "Return exactly one JSON object, with no markdown fences and no extra text."
                )
                raw = ask_llm(
                    repair_msg,
                    model=model,
                    temperature=0.0,
                    max_tokens=self.max_tokens_for_mode(mode),
                    system_msg=system_msg,
                    reasoning_effort=reasoning_effort,
                    response_format=response_format,
                    seed=seed,
                    return_metadata=True,
                )
                raw_text, response_meta = raw if isinstance(raw, tuple) else (str(raw), {})
                try:
                    payload = extract_json_payload_from_llm_text(raw_text)
                except Exception:
                    repair_count += 1
                    parse_status = "final_repair"
                    final_repair_msg = (
                        "Convert the following invalid model output into exactly one valid JSON object "
                        "matching the required schema shape. Preserve the intended content, but fix escaping, "
                        "quoting, and structure. Return only the repaired JSON object.\n\n"
                        f"Schema shape:\n{json.dumps(schema_hint, indent=2, sort_keys=True)}\n\n"
                        f"Invalid model output:\n{raw_text}"
                    )
                    raw = ask_llm(
                        final_repair_msg,
                        model=model,
                        temperature=0.0,
                        max_tokens=self.max_tokens_for_mode(mode),
                        system_msg=system_msg,
                        reasoning_effort="minimal",
                        response_format=response_format,
                        seed=seed,
                        return_metadata=True,
                    )
                    raw_text, response_meta = raw if isinstance(raw, tuple) else (str(raw), {})
                    payload = extract_json_payload_from_llm_text(raw_text)

            if not isinstance(payload, dict):
                raise RuntimeError("LLM proposal payload must be a JSON object.")

            response_envelope = {
                "raw_text": raw_text,
                "payload": payload,
            }
            response_digest = _canonical_digest(response_envelope)
            receipt = LLMSupplementReceipt(
                proposal_type=proposal_type.value,
                mode=mode.value,
                request_digest=request_digest,
                response_digest=response_digest,
                provider=self.provider,
                model=model,
                base_url=self.base_url,
                seed=seed,
                system_fingerprint=str(response_meta.get("system_fingerprint", "")).strip() or None,
                parse_status=parse_status,
                repair_count=repair_count,
                raw_text=raw_text,
                payload=dict(payload),
            ).to_dict()

            return LLMSupplementResult(
                payload=payload,
                source="llm",
                provider=self.provider,
                model=model,
                raw_text=raw_text,
                receipt=receipt,
            )
        except Exception as exc:
            if self.policy == "required":
                raise
            response_envelope = {
                "raw_text": raw_text,
                "payload": payload,
                "error": str(exc),
            }
            response_digest = _canonical_digest(response_envelope)
            receipt = LLMSupplementReceipt(
                proposal_type=proposal_type.value,
                mode=mode.value,
                request_digest=request_digest,
                response_digest=response_digest,
                provider=self.provider,
                model=model,
                base_url=self.base_url,
                seed=seed,
                system_fingerprint=str(response_meta.get("system_fingerprint", "")).strip() or None,
                parse_status=parse_status,
                repair_count=repair_count,
                error=str(exc),
                raw_text=raw_text,
                payload=dict(payload) if isinstance(payload, dict) else None,
            ).to_dict()
            return LLMSupplementResult(
                payload=None,
                source="heuristic",
                provider=self.provider,
                model=model,
                error=str(exc),
                receipt=receipt,
            )
