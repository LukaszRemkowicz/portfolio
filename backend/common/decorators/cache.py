# common/decorators/cache.py

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable

from django.core.cache import cache
from django.http import JsonResponse

from common.constants import INFINITE_CACHE_TIMEOUT

logger = logging.getLogger("core.cache")


def cache_response(timeout: int = INFINITE_CACHE_TIMEOUT, key_prefix: str = "api_cache"):
    """
    Decorator for DRF view actions/methods to cache response data.
    Supports ETags for 304 Not Modified responses.
    """

    def decorator(view_func: Callable):
        @wraps(view_func)
        def _wrapped_view(request: Any, *args: Any, **kwargs: Any) -> Any:
            if request.method != "GET":
                return view_func(request, *args, **kwargs)

            # Construct cache key
            path = getattr(request, "path", "unknown")
            params = getattr(request, "query_params", getattr(request, "GET", {}))
            query_params = sorted(params.items())
            lang = getattr(request, "LANGUAGE_CODE", "en")

            # Hash query params to avoid illegal characters (brackets, quotes) and length issues
            params_str = json.dumps(query_params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode("utf-8")).hexdigest()

            cache_key = f"{key_prefix}:{path}:{lang}:{params_hash}"

            # Check cache
            cached_package = cache.get(cache_key)
            if cached_package is not None:
                # Handle legacy data (before ETag implementation)
                if not isinstance(cached_package, dict):
                    logger.debug(f"Legacy cache format detected [Key: {cache_key}]. Clearing.")
                    cache.delete(cache_key)
                else:
                    data = cached_package.get("data")
                    etag = cached_package.get("etag")
                    logger.debug(f"Cache HIT [Key: {cache_key}]")
                    response = JsonResponse(data, safe=False)
                    if etag:
                        response["ETag"] = etag
                    return response

            logger.debug(f"Cache MISS [Key: {cache_key}]")
            response = view_func(request, *args, **kwargs)

            # Cache successful GET responses
            if hasattr(response, "status_code") and response.status_code == 200:
                if hasattr(response, "data"):
                    data = response.data

                    if data is None:
                        logger.warning(f"Response data is None for key {cache_key}. Not caching.")
                        return response

                    # Generate ETag from data
                    content = json.dumps(data, sort_keys=True).encode("utf-8")
                    etag = f'"{hashlib.md5(content).hexdigest()}"'

                    logger.debug(f"Caching Data [Key: {cache_key}]")
                    cache.set(cache_key, {"data": data, "etag": etag}, timeout)

                    response["ETag"] = etag
                else:
                    # Rendered responses (from dispatch decoration) won't have .data
                    logger.debug(
                        f"Response has no data attribute [Key: {cache_key}] - skipping cache"
                    )

            return response

        return _wrapped_view

    return decorator
