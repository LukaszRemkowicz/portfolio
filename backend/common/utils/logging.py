"""Shared logging helpers and JSON logging primitives.

The backend writes structured logs to Docker stdout so downstream tooling can
parse them reliably. This module provides:

- request-scoped logging context via ``contextvars``
- a logging filter that injects request metadata into every record
- a JSON formatter that emits one structured JSON object per line
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import UTC, datetime
from logging import Filter, Formatter, LogRecord
from typing import Any

_REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="")
_REQUEST_METHOD: ContextVar[str] = ContextVar("request_method", default="")
_REQUEST_PATH: ContextVar[str] = ContextVar("request_path", default="")
_REQUEST_HOST: ContextVar[str] = ContextVar("request_host", default="")

_STANDARD_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


def sanitize_for_logging(value: str | None) -> str:
    """Sanitize a string for structured logging."""
    if not value:
        return ""

    sanitized = value.replace("\n", " ").replace("\r", " ")
    if len(sanitized) > 1000:
        return sanitized[:997] + "..."
    return sanitized


def set_request_log_context(
    *,
    request_id: str,
    method: str,
    path: str,
    host: str,
) -> None:
    """Store request context so all logs emitted in-request can include it."""
    _REQUEST_ID.set(sanitize_for_logging(request_id))
    _REQUEST_METHOD.set(sanitize_for_logging(method))
    _REQUEST_PATH.set(sanitize_for_logging(path))
    _REQUEST_HOST.set(sanitize_for_logging(host))


def clear_request_log_context() -> None:
    """Clear request-scoped logging context after the request finishes."""
    _REQUEST_ID.set("")
    _REQUEST_METHOD.set("")
    _REQUEST_PATH.set("")
    _REQUEST_HOST.set("")


class RequestContextFilter(Filter):
    """Inject request-scoped metadata into every log record."""

    def __init__(self, environment: str = "development") -> None:
        super().__init__()
        self.environment = environment

    def filter(self, record: LogRecord) -> bool:
        record.environment = self.environment
        record.request_id = _REQUEST_ID.get()
        record.request_method = _REQUEST_METHOD.get()
        record.request_path = _REQUEST_PATH.get()
        record.request_host = _REQUEST_HOST.get()
        return True


class JsonFormatter(Formatter):
    """Emit one JSON object per log record for Docker stdout consumption."""

    def format(self, record: LogRecord) -> str:
        payload = self._build_base_payload(record)
        self._add_request_context(payload, record)
        self._add_extra_fields(payload, record)
        self._add_exception_details(payload, record)
        return json.dumps(payload, ensure_ascii=True, default=str)

    def _build_base_payload(self, record: LogRecord) -> dict[str, Any]:
        return {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
            "message": sanitize_for_logging(record.getMessage()),
            "environment": getattr(record, "environment", ""),
        }

    def _add_request_context(self, payload: dict[str, Any], record: LogRecord) -> None:
        for field_name in ("request_id", "request_method", "request_path", "request_host"):
            value = getattr(record, field_name, "")
            if value:
                payload[field_name] = value

    def _add_extra_fields(self, payload: dict[str, Any], record: LogRecord) -> None:
        excluded_fields = {
            "environment",
            "request_id",
            "request_method",
            "request_path",
            "request_host",
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_FIELDS or key in excluded_fields or key.startswith("_"):
                continue
            if value is None:
                continue
            payload[key] = self._serialize_extra_value(value)

    def _add_exception_details(self, payload: dict[str, Any], record: LogRecord) -> None:
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack"] = sanitize_for_logging(self.formatStack(record.stack_info))

    def _serialize_extra_value(self, value: Any) -> str | int | float | bool:
        if isinstance(value, str):
            return sanitize_for_logging(value)
        if isinstance(value, (int, float, bool)):
            return value
        return sanitize_for_logging(repr(value))
