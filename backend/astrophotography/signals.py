"""Cache invalidation signals for astrophotography content.

This module keeps two cache layers in sync after astrophotography content changes:

- backend API cache, cleared via ``CacheService``
- frontend SSR shell cache, cleared via ``invalidate_frontend_ssr_cache_task``

Why the frontend cache must also be cleared:
- the Node SSR server caches shared shell fragments such as
  ``latest-astro-images``, ``travel-highlights``, ``background``, and ``settings``
- clearing only the backend cache would still leave stale SSR HTML until the
  frontend cache expires naturally

Each receiver therefore invalidates the backend cache keys and, when the
frontend shell depends on the changed data, also clears the matching SSR tag.
"""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService

from .models import AstroImage, MainPageBackgroundImage, MainPageLocation, Tag


@receiver([post_save, post_delete], sender=AstroImage)
@receiver([post_save, post_delete], sender="astrophotography.AstroImageTranslation")
def invalidate_astroimage_cache(sender, instance, **kwargs):
    """Clear gallery/travel caches after astro image content changes.

    Clears:
    - backend astrophotography API cache
    - frontend SSR tags: ``latest-astro-images`` and ``travel-highlights``

    We clear the frontend tags because homepage/latest-image shells and travel
    highlight shells embed astrophotography data.
    """
    CacheService.invalidate_astrophotography_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["latest-astro-images", "travel-highlights"])


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
    """Clear landing/settings caches when one image's derived hours change.

    Clears:
    - backend landing-page/settings cache
    - frontend SSR tag: ``settings``

    We clear ``settings`` because the public landing-page total is derived from
    ``AstroImage.calculated_exposure_hours`` and exposed through the settings API.
    """
    if update_fields is not None and "calculated_exposure_hours" not in update_fields:
        return

    previous_value = getattr(instance, "_previous_calculated_exposure_hours", None)
    current_value = instance.calculated_exposure_hours

    if previous_value == current_value:
        return

    CacheService.invalidate_landing_page_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["settings"])


@receiver(post_delete, sender=AstroImage)
def recalculate_total_time_spent_after_astroimage_delete(sender, instance, **kwargs):
    """Clear settings caches after deleting an image that contributes to the total.

    Clears:
    - backend landing-page/settings cache
    - frontend SSR tag: ``settings``

    Deleting an image changes the derived landing-page total, so the settings
    payload and SSR shell must both be refreshed.
    """
    CacheService.invalidate_landing_page_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["settings"])


@receiver([post_save, post_delete], sender=Tag)
@receiver([post_save, post_delete], sender="astrophotography.TagTranslation")
def invalidate_tag_cache(sender, instance, **kwargs):
    """Clear backend astrophotography cache when tags or tag translations change.

    Clears:
    - backend astrophotography API cache

    No frontend tag is cleared here because tag changes do not map directly to a
    dedicated SSR shell resource in the same way as latest images or settings.
    """
    CacheService.invalidate_astrophotography_cache()


@receiver([post_save, post_delete], sender=MainPageLocation)
@receiver([post_save, post_delete], sender="astrophotography.MainPageLocationTranslation")
def invalidate_travel_cache(sender, instance, **kwargs):
    """Clear travel caches when main-page travel slider content changes.

    Clears:
    - backend travel API cache
    - frontend SSR tag: ``travel-highlights``

    The frontend tag is required because the SSR shell caches the travel
    highlights section separately from the backend API response cache.
    """
    CacheService.invalidate_travel_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["travel-highlights"])


@receiver([post_save, post_delete], sender=MainPageBackgroundImage)
@receiver([post_save, post_delete], sender="astrophotography.MainPageBackgroundImageTranslation")
def invalidate_background_cache(sender, instance, **kwargs):
    """Clear background caches when homepage background images change.

    Clears:
    - backend astrophotography API cache
    - frontend SSR tag: ``background``

    The background shell is SSR-cached independently, so backend invalidation
    alone would not refresh the rendered page background.
    """
    CacheService.invalidate_astrophotography_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["background"])
