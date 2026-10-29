# See MODULES.md for the repository module map before editing.
"""Invocation-scoped transport from a Python skill child to its parent host."""

from __future__ import annotations

import json
import secrets
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from realized_core_runtime.host_abi import (
    required_authority_for_host_broker,
    validate_host_broker_invocation,
)
from realized_host_interaction.realizers import (
    HostBrokerInvocation,
    HostRealizerProvider,
)


PYTHON_SKILL_HOST_ENDPOINT_ENV = "BSSC_PYTHON_SKILL_HOST_ENDPOINT"
PYTHON_SKILL_HOST_TOKEN_ENV = "BSSC_PYTHON_SKILL_HOST_TOKEN"
PYTHON_SKILL_HOST_PROVIDER_REQUIRED_ENV = "BSSC_PYTHON_SKILL_HOST_PROVIDER_REQUIRED"
_MAX_REQUEST_BYTES = 1_048_576


def _declared_broker_identities(context: Mapping[str, Any]) -> frozenset[str]:
    raw_identities = context.get("declared_host_brokers", [])
    if not isinstance(raw_identities, Sequence) or isinstance(
        raw_identities,
        (str, bytes, bytearray),
    ):
        return frozenset()
    return frozenset(
        identity
        for item in raw_identities
        if (identity := str(item).strip())
    )


def _bridge_denial(
    context: Mapping[str, Any],
    *,
    broker_name: str,
    arguments: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Validate child input against authoritative parent invocation state."""

    if bool(context.get("strict_realizer_declaration")) and (
        broker_name not in _declared_broker_identities(context)
    ):
        return None, {
            "status": "error",
            "broker": broker_name,
            "error": f"Skill declaration does not bind the exact host broker {broker_name!r}.",
        }
    admission = context.get("admission", {})
    admission_record = dict(admission) if isinstance(admission, Mapping) else {}
    admission_status = str(admission_record.get("status", "admitted")).strip().lower()
    admitted = bool(
        admission_record.get(
            "admitted",
            admission_status in {"admitted", "legacy_implicit_admit"},
        )
    )
    if not admitted:
        return None, {
            "status": "error",
            "broker": broker_name,
            "error": str(admission_record.get("rationale", "")).strip()
            or "Governed skill is not admitted for broker use.",
        }
    required_authority = required_authority_for_host_broker(broker_name)
    grants = context.get("grants", [])
    grant_records = (
        [dict(item) for item in grants if isinstance(item, Mapping)]
        if isinstance(grants, Sequence) and not isinstance(grants, (str, bytes, bytearray))
        else []
    )
    if required_authority and not any(
        str(item.get("authority", "")).strip() == required_authority
        and str(item.get("id", "")).strip()
        for item in grant_records
    ):
        return None, {
            "status": "error",
            "broker": broker_name,
            "error": (
                f"Runtime grants do not cover required authority {required_authority} "
                f"for {broker_name}."
            ),
        }
    normalized_arguments, abi_error = validate_host_broker_invocation(
        broker_name,
        arguments,
    )
    if normalized_arguments is None:
        return None, {
            "status": "error",
            "broker": broker_name,
            "error": abi_error,
        }
    return normalized_arguments, None


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


@contextmanager
def python_skill_host_bridge(
    provider: HostRealizerProvider,
    *,
    governance_context: Mapping[str, Any],
) -> Iterator[dict[str, str]]:
    """Expose one provider only for the lifetime of one child invocation."""

    token = secrets.token_urlsafe(32)
    authoritative_context = dict(governance_context)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
            if self.path != "/broker":
                _json_response(self, 404, {"status": "error", "error": "Unknown bridge path."})
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                content_length = 0
            if content_length <= 0 or content_length > _MAX_REQUEST_BYTES:
                _json_response(
                    self,
                    413,
                    {"status": "error", "error": "Invalid or oversized broker request."},
                )
                return
            try:
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            except Exception as exc:
                _json_response(
                    self,
                    400,
                    {"status": "error", "error": f"Invalid broker request JSON: {exc}"},
                )
                return
            if not isinstance(payload, Mapping) or not secrets.compare_digest(
                str(payload.get("token", "")),
                token,
            ):
                _json_response(
                    self,
                    403,
                    {"status": "error", "error": "Invalid invocation-scoped bridge token."},
                )
                return
            broker_name = str(payload.get("broker_name", "")).strip()
            arguments = payload.get("arguments", {})
            if not broker_name or not isinstance(arguments, Mapping):
                _json_response(
                    self,
                    400,
                    {"status": "error", "error": "Broker identity and object arguments are required."},
                )
                return
            normalized_arguments, denial = _bridge_denial(
                authoritative_context,
                broker_name=broker_name,
                arguments=arguments,
            )
            if denial is not None:
                _json_response(self, 403, denial)
                return
            try:
                result = provider.invoke_broker(
                    HostBrokerInvocation(
                        identity=broker_name,
                        arguments=normalized_arguments or {},
                        governance_context=authoritative_context,
                    )
                )
            except Exception as exc:
                result = {
                    "status": "error",
                    "broker": broker_name,
                    "error": str(exc),
                }
            _json_response(self, 200, result)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01),
        daemon=True,
    )
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield {
            PYTHON_SKILL_HOST_ENDPOINT_ENV: f"http://{host}:{port}/broker",
            PYTHON_SKILL_HOST_TOKEN_ENV: token,
            PYTHON_SKILL_HOST_PROVIDER_REQUIRED_ENV: "1",
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def request_parent_host_broker(
    *,
    endpoint: str,
    token: str,
    broker_name: str,
    arguments: Mapping[str, Any],
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Send one bounded broker request to the invocation-scoped parent bridge."""

    encoded = json.dumps(
        {
            "token": token,
            "broker_name": broker_name,
            "arguments": dict(arguments),
        },
        sort_keys=True,
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=max(1.0, timeout_seconds)) as response:
            encoded_response = response.read(_MAX_REQUEST_BYTES + 1)
            if len(encoded_response) > _MAX_REQUEST_BYTES:
                raise ValueError("Parent host bridge response exceeded the size limit.")
            payload = json.loads(encoded_response.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            error_payload = json.loads(exc.read(_MAX_REQUEST_BYTES + 1).decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            error_payload = None
        finally:
            exc.close()
        if isinstance(error_payload, Mapping):
            return dict(error_payload)
        return {
            "status": "error",
            "broker": broker_name,
            "error": f"Parent host bridge rejected the request: HTTP {exc.code}.",
        }
    except (OSError, urllib.error.URLError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "status": "error",
            "broker": broker_name,
            "error": f"Parent host bridge request failed: {exc}",
        }
    if not isinstance(payload, Mapping):
        return {
            "status": "error",
            "broker": broker_name,
            "error": "Parent host bridge returned a non-object response.",
        }
    return dict(payload)


__all__ = [
    "PYTHON_SKILL_HOST_ENDPOINT_ENV",
    "PYTHON_SKILL_HOST_PROVIDER_REQUIRED_ENV",
    "PYTHON_SKILL_HOST_TOKEN_ENV",
    "python_skill_host_bridge",
    "request_parent_host_broker",
]
