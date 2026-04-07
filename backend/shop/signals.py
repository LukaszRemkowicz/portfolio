# backend/shop/signals.py
"""Cache invalidation signals for shop content.

Keeps two cache layers in sync after shop product changes:
- backend API cache, cleared via CacheService
- frontend SSR shell cache, cleared via invalidate_frontend_ssr_cache_task
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService

from .models import ShopProduct


@receiver([post_save, post_delete], sender=ShopProduct)
@receiver([post_save, post_delete], sender="shop.ShopProductTranslation")
def invalidate_shop_cache(sender, instance, **kwargs):
    """Clear shop caches after product content changes.

    Clears:
    - backend shop API cache
    - frontend SSR tag: ``shop``
    """
    CacheService.invalidate_shop_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["shop"])
