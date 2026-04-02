"""Shared Django middleware used across the portfolio backend.

This module keeps lightweight cross-cutting request behavior in one place:

- request correlation via ``X-Request-ID`` for tracing across services
- locale activation from the ``lang`` query parameter
"""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from django.utils import translation

logger = logging.getLogger("django.request")


class RequestCorrelationMiddleware:
    """Attach and propagate a request correlation ID for each request.

    The middleware reuses an incoming ``X-Request-ID`` header when present or
    generates a new UUID when the request enters Django without one. The value
    is stored on ``request.request_id``, echoed back on the response, and
    included in the request log line together with method, path, status, host,
    and duration.

    This makes it possible to correlate a single request across the frontend
    server, backend, nginx, and monitoring pipelines.
    """

    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        request_id = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        request.request_id = request_id

        started_at = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - started_at) * 1000)

        response["X-Request-ID"] = request_id

        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s host=%s",
            request_id,
            request.method,
            request.get_full_path(),
            getattr(response, "status_code", "unknown"),
            duration_ms,
            request.get_host(),
        )

        return response


class QueryParameterLocaleMiddleware:
    """Activate a supported locale from the ``lang`` query parameter.

    This middleware allows URL-level language selection to override the
    browser's ``Accept-Language`` header when a supported language code is
    present in the query string.
    """

    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        # 1. Check for 'lang' parameter in the query string
        lang = request.GET.get("lang")

        if lang:
            # Normalize to lowercase and check if supported
            lang = lang.lower()
            if translation.check_for_language(lang):
                translation.activate(lang)
                request.LANGUAGE_CODE = translation.get_language()

        return self.get_response(request)
