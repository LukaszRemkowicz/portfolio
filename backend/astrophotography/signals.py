from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService
from core.tasks import (
    calculate_astroimage_exposure_hours_task,
    recalculate_landing_page_total_time_spent_task,
)

from .models import AstroImage, MainPageBackgroundImage, MainPageLocation, Tag


@receiver([post_save, post_delete], sender=AstroImage)
@receiver([post_save, post_delete], sender="astrophotography.AstroImageTranslation")
def invalidate_astroimage_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["latest-astro-images", "travel-highlights"])


@receiver(post_save, sender="astrophotography.AstroImageTranslation")
def recalculate_landing_page_total_time_spent(sender, instance, **kwargs):
    if getattr(instance, "language_code", None) != "en":
        return

    exposure_details = getattr(instance, "exposure_details", "")
    previous_exposure_details = getattr(instance, "_previous_exposure_details", None)

    if not exposure_details or exposure_details == previous_exposure_details:
        return

    calculate_astroimage_exposure_hours_task.delay_on_commit(str(instance.master_id))


@receiver(pre_save, sender="astrophotography.AstroImageTranslation")
def store_previous_exposure_details(sender, instance, **kwargs):
    if getattr(instance, "language_code", None) != "en":
        instance._previous_exposure_details = None
        return

    if not instance.pk:
        instance._previous_exposure_details = None
        return

    instance._previous_exposure_details = (
        sender.objects.filter(pk=instance.pk).values_list("exposure_details", flat=True).first()
    )


@receiver(pre_save, sender=AstroImage)
def store_previous_calculated_exposure_hours(sender, instance, **kwargs):
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
    recalculate_landing_page_total_time_spent_task.delay_on_commit(str(instance.pk))


@receiver([post_save, post_delete], sender=Tag)
@receiver([post_save, post_delete], sender="astrophotography.TagTranslation")
def invalidate_tag_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()


@receiver([post_save, post_delete], sender=MainPageLocation)
@receiver([post_save, post_delete], sender="astrophotography.MainPageLocationTranslation")
def invalidate_travel_cache(sender, instance, **kwargs):
    CacheService.invalidate_travel_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["travel-highlights"])


@receiver([post_save, post_delete], sender=MainPageBackgroundImage)
@receiver([post_save, post_delete], sender="astrophotography.MainPageBackgroundImageTranslation")
def invalidate_background_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["background"])
