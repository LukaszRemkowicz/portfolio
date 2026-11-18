from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from django.dispatch import receiver

from core.cache_service import CacheService

from .models import LandingPageSettings


@receiver(pre_delete, sender="astrophotography.AstroImage")
@receiver(pre_delete, sender="astrophotography.MainPageBackgroundImage")
@receiver(pre_delete, sender="programming.ProjectImage")
@receiver(pre_delete, sender="shop.ShopProduct")
@receiver(pre_delete, sender="shop.ShopSettings")
@receiver(pre_delete, sender="users.User")
def delete_image_variant_files_with_owner(sender, instance, **kwargs) -> None:
    """Delete variant rows transactionally and their files after commit."""
    if hasattr(instance, "variants"):
        instance.variants.using(kwargs["using"]).all().delete()


@receiver([post_save, post_delete], sender=LandingPageSettings)
def invalidate_settings_cache(sender, instance, **kwargs):
    """Clear API caches when landing-page settings change."""
    CacheService.invalidate_landing_page_cache()
    CacheService.invalidate_astrophotography_cache()
    CacheService.invalidate_shop_cache()


@receiver(m2m_changed, sender=LandingPageSettings.latest_filters.through)
def invalidate_settings_m2m_cache(sender, instance, action, **kwargs):
    """
    Clears cache when the Many-to-Many 'latest_filters' field is modified.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        invalidate_settings_cache(sender=LandingPageSettings, instance=instance)
