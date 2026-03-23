from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService

from .models import LandingPageSettings


@receiver([post_save, post_delete], sender=LandingPageSettings)
def invalidate_settings_cache(sender, instance, **kwargs):
    """
    Triggers both Backend API cache invalidation and Frontend SSR cache invalidation.
    """
    # 1. Clear Backend API Cache
    CacheService.invalidate_landing_page_cache()

    # 2. Clear Frontend SSR Cache (Async)
    invalidate_frontend_ssr_cache_task.delay_on_commit(["settings"])


@receiver(m2m_changed, sender=LandingPageSettings.latest_filters.through)
def invalidate_settings_m2m_cache(sender, instance, action, **kwargs):
    """
    Clears cache when the Many-to-Many 'latest_filters' field is modified.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        invalidate_settings_cache(sender=LandingPageSettings, instance=instance)
