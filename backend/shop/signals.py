# backend/shop/signals.py
"""Cache invalidation signals for shop content."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.cache_service import CacheService

from .models import ShopProduct, ShopSettings


@receiver([post_save, post_delete], sender=ShopSettings)
@receiver([post_save, post_delete], sender="shop.ShopSettingsTranslation")
@receiver([post_save, post_delete], sender=ShopProduct)
@receiver([post_save, post_delete], sender="shop.ShopProductTranslation")
def invalidate_shop_cache(sender, instance, **kwargs):
    """Clear shop API cache after product content changes."""
    CacheService.invalidate_shop_cache()
