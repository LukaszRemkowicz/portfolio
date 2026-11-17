"""Cache invalidation signals for astrophotography content."""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from core.cache_service import CacheService
from core.models import ImageVariant

from .models import AstroImage, MainPageBackgroundImage, MainPageLocation, Place, Tag


@receiver([post_save, post_delete], sender=AstroImage)
@receiver([post_save, post_delete], sender="astrophotography.AstroImageTranslation")
def invalidate_astroimage_cache(sender, instance, **kwargs):
    """Clear gallery and travel caches after astro image content changes."""
    CacheService.invalidate_astrophotography_cache()
    CacheService.invalidate_travel_cache()


@receiver([post_save, post_delete], sender=ImageVariant)
def invalidate_cache_for_image_variant_change(sender, instance: ImageVariant, **kwargs) -> None:
    """Clear API caches when generated image files change."""
    owner = instance.owner
    if isinstance(owner, AstroImage):
        CacheService.invalidate_astrophotography_cache()
        CacheService.invalidate_travel_cache()
        return

    if isinstance(owner, MainPageBackgroundImage):
        CacheService.invalidate_astrophotography_cache()


@receiver(pre_save, sender=AstroImage)
def store_previous_calculated_exposure_hours(sender, instance, **kwargs):
    """Capture the persisted exposure-hour value for post-save change detection."""
    if not instance.pk:
        instance._previous_calculated_exposure_hours = None
        return

    instance._previous_calculated_exposure_hours = (
        sender.objects.filter(pk=instance.pk)
        .values_list("calculated_exposure_hours", flat=True)
        .first()
    )


@receiver(post_save, sender=AstroImage)
def invalidate_settings_cache_when_calculated_exposure_hours_changes(
    sender, instance, update_fields=None, **kwargs
):
    """Clear landing/settings cache when derived hours change."""
    if update_fields is not None and "calculated_exposure_hours" not in update_fields:
        return

    previous_value = getattr(instance, "_previous_calculated_exposure_hours", None)
    current_value = instance.calculated_exposure_hours

    if previous_value == current_value:
        return

    CacheService.invalidate_landing_page_cache()


@receiver(post_delete, sender=AstroImage)
def recalculate_total_time_spent_after_astroimage_delete(sender, instance, **kwargs):
    """Clear settings cache after deleting an image that contributes to the total."""
    CacheService.invalidate_landing_page_cache()


@receiver([post_save, post_delete], sender=Tag)
@receiver([post_save, post_delete], sender="astrophotography.TagTranslation")
def invalidate_tag_cache(sender, instance, **kwargs):
    """Clear astrophotography and travel caches when tags change."""
    CacheService.invalidate_astrophotography_cache()
    CacheService.invalidate_travel_cache()


@receiver([post_save, post_delete], sender=Place)
@receiver([post_save, post_delete], sender="astrophotography.PlaceTranslation")
def invalidate_place_cache(sender, instance, **kwargs):
    """Clear backend astrophotography and travel caches when places change."""
    CacheService.invalidate_astrophotography_cache()
    CacheService.invalidate_travel_cache()


@receiver([post_save, post_delete], sender=MainPageLocation)
@receiver([post_save, post_delete], sender="astrophotography.MainPageLocationTranslation")
def invalidate_travel_cache(sender, instance, **kwargs):
    """Clear travel cache when main-page travel slider content changes."""
    CacheService.invalidate_travel_cache()


@receiver([post_save, post_delete], sender=MainPageBackgroundImage)
@receiver([post_save, post_delete], sender="astrophotography.MainPageBackgroundImageTranslation")
def invalidate_background_cache(sender, instance, **kwargs):
    """Clear astrophotography cache when homepage background images change."""
    CacheService.invalidate_astrophotography_cache()
