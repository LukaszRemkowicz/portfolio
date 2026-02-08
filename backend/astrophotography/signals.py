# astrophotography/signals.py

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.cache_service import CacheService

from .models import AstroImage, MainPageBackgroundImage, MainPageLocation, Tag


@receiver([post_save, post_delete], sender=AstroImage)
@receiver([post_save, post_delete], sender="astrophotography.AstroImageTranslation")
def invalidate_astroimage_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()


@receiver([post_save, post_delete], sender=Tag)
@receiver([post_save, post_delete], sender="astrophotography.TagTranslation")
def invalidate_tag_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()


@receiver([post_save, post_delete], sender=MainPageLocation)
@receiver([post_save, post_delete], sender="astrophotography.MainPageLocationTranslation")
def invalidate_travel_cache(sender, instance, **kwargs):
    CacheService.invalidate_travel_cache()


@receiver([post_save, post_delete], sender=MainPageBackgroundImage)
@receiver([post_save, post_delete], sender="astrophotography.MainPageBackgroundImageTranslation")
def invalidate_background_cache(sender, instance, **kwargs):
    CacheService.invalidate_astrophotography_cache()
