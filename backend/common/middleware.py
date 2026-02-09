# backend/common/middleware.py
from typing import Any, Callable

from django.utils import translation


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
