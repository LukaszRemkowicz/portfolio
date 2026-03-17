import hashlib
import json
import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Type

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseNotModified, JsonResponse

logger = logging.getLogger("core.cache")


class BaseCacheStrategy(ABC):
    """
    Abstract interface for defining how a response should be cached.
    Allows for different caching logic per view (e.g., custom keys, different data formats).
    """

    @abstractmethod
    def get_cache_key(self, request: Any, key_prefix: str) -> str:
        """Construct a unique cache key for the request."""
        raise NotImplementedError

    @abstractmethod
    def get_response_data(self, response: Any, cache_key: str) -> Any | None:
        """Extract serializable data from the response."""
        raise NotImplementedError


class DefaultCacheStrategy(BaseCacheStrategy):
    """
    Default implementation of the Strategy Pattern for caching.
    Handles standard DRF and Django JsonResponses.
    """

    def get_cache_key(self, request: Any, key_prefix: str) -> str:
        path = getattr(request, "path", "unknown")
        params = getattr(request, "query_params", getattr(request, "GET", {}))
        query_params = sorted(params.items())
        lang = getattr(request, "LANGUAGE_CODE", "en")

        # Hash query params to avoid illegal characters and length issues
        params_str = json.dumps(query_params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode("utf-8")).hexdigest()

        return f"{key_prefix}:{path}:{lang}:{params_hash}"

    def get_response_data(self, response: Any, cache_key: str) -> Any | None:
        # Detect if this is a standard Django response or DRF response
        if hasattr(response, "data"):
            return response.data

        # For rendered responses (like JsonResponse), extract content safely
        try:
            return json.loads(response.content)
        except (AttributeError, ValueError):
            logger.debug(f"Response has no parsable content [Key: {cache_key}]")
            return None


def cache_response(
    timeout: int | None = None,
    key_prefix: str = "api_cache",
    strategy_class: Type[BaseCacheStrategy] = DefaultCacheStrategy,
):
    """
    Decorator for DRF view actions/methods to cache response data using a Strategy Pattern.
    Supports ETags for 304 Not Modified responses.
    """
    strategy = strategy_class()

    def decorator(view_func: Callable):
        @wraps(view_func)
        def _wrapped_view(request: Any, *args: Any, **kwargs: Any) -> Any:
            if request.method != "GET":
                return view_func(request, *args, **kwargs)

            actual_timeout = timeout or settings.INFINITE_CACHE_TIMEOUT
            cache_key = strategy.get_cache_key(request, key_prefix)

            # Check cache
            cached_package = cache.get(cache_key)
            if cached_package is not None and isinstance(cached_package, dict):
                data = cached_package.get("data")
                etag = cached_package.get("etag")
                logger.debug(f"Cache HIT [Key: {cache_key}]")

                # Fast path for ETag validation (304 Not Modified)
                if etag and request.META.get("HTTP_IF_NONE_MATCH") == etag:
                    return HttpResponseNotModified()

                response = JsonResponse(data, safe=False)
                if etag:
                    response["ETag"] = etag
                return response

            if cached_package is not None:
                # Handle legacy non-dict data
                cache.delete(cache_key)

            logger.debug(f"Cache MISS [Key: {cache_key}]")
            response = view_func(request, *args, **kwargs)

            # Cache successful GET responses
            if getattr(response, "status_code", None) == 200:
                data = strategy.get_response_data(response, cache_key)
                if data is not None:
                    # Generate ETag and save to cache
                    content = json.dumps(data, sort_keys=True).encode("utf-8")
                    etag = f'"{hashlib.md5(content).hexdigest()}"'

                    logger.debug(f"Caching Data [Key: {cache_key}]")
                    cache.set(cache_key, {"data": data, "etag": etag}, actual_timeout)
                    response["ETag"] = etag

            return response

        return _wrapped_view

    return decorator
