import logging
import warnings

from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheService:
    """
    Centralized service for cache key management and invalidation.
    """

    @staticmethod
    def clear_prefix(prefix: str) -> None:
        """
        Clears all keys starting with the given prefix.
        Note: On Redis, this uses SCAN to avoid blocking.
        """
        pattern = f"*{prefix}*"

        if hasattr(cache, "delete_pattern"):
            # django-redis specific helper
            cache.delete_pattern(pattern)
        elif hasattr(cache, "_cache") and hasattr(cache._cache, "get_client"):
            # Django's native RedisCache (Django 4.0+)
            try:
                client = cache._cache.get_client()
                cursor = 0
                while True:
                    cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
                    if keys:
                        client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.warning(f"Failed to scan and delete cache keys with pattern {pattern}: {e}")
                cache.clear()
        else:
            # Fallback for other backends (less efficient)
            warnings.warn(
                "Cache backend does not support delete_pattern. Global clear might be slow.",
                UserWarning,
            )
            cache.clear()

    @staticmethod
    def invalidate_user_cache() -> None:
        """Invalidates user-related API cache."""
        CacheService.clear_prefix("api_cache:/v1/profile")
        logger.info("Invalidated user cache")

    @staticmethod
    def invalidate_astrophotography_cache() -> None:
        """Invalidates astrophotography-related API cache."""
        CacheService.clear_prefix("api_cache:/v1/image")
        CacheService.clear_prefix("api_cache:/v1/tags")
        CacheService.clear_prefix("api_cache:/v1/categories")
        CacheService.clear_prefix("api_cache:/v1/background")
        logger.info("Invalidated astrophotography cache")

    @staticmethod
    def invalidate_travel_cache() -> None:
        """Invalidates travel-related API cache."""
        CacheService.clear_prefix("api_cache:/v1/travel-highlights")
        CacheService.clear_prefix("api_cache:/v1/travel/")
        logger.info("Invalidated travel cache")
