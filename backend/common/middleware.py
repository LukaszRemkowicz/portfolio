# backend/common/middleware.py
import logging
import time
import uuid
from typing import Any, Callable

from django.utils import translation

logger = logging.getLogger("django.request")


class RequestCorrelationMiddleware:
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
    """
    Middleware that activates the language based on the 'lang' query parameter.
    This allows overriding the browser's Accept-Language header via URL.
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
