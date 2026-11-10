import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheService:
    """
    Centralized service for cache key management and invalidation.
    """

    @staticmethod
    def clear_prefix(prefix: str) -> None:
        """
        Clears the cache. DatabaseCache cannot delete keys by prefix, so the whole
        cache is cleared; `prefix` is kept only to document what is being invalidated.
        """
        logger.debug("Clearing cache (requested prefix: %s)", prefix)
        cache.clear()

    @staticmethod
    def invalidate_user_cache() -> None:
        """Invalidates user-related API cache."""
        CacheService.clear_prefix("api_cache:/v1/profile")
        logger.info("Invalidated user cache")

    @staticmethod
    def invalidate_astrophotography_cache() -> None:
        """Invalidates astrophotography-related API cache."""
        CacheService.clear_prefix("api_cache:/v1/astroimages")
        logger.info("Invalidated astrophotography cache")

    @staticmethod
    def invalidate_travel_cache() -> None:
        """Invalidates travel-related API cache."""
        CacheService.clear_prefix("api_cache:/v1/travel-highlights")
        logger.info("Invalidated travel cache")

    @staticmethod
    def invalidate_landing_page_cache() -> None:
        """Invalidates landing-page related API cache."""
        CacheService.clear_prefix("api_cache:/v1/settings")
        logger.info("Invalidated landing page cache")

    @staticmethod
    def invalidate_shop_cache() -> None:
        """Invalidates shop API cache."""
        CacheService.clear_prefix("api_cache_shop:/v1/shop")
        logger.info("Invalidated shop cache")
