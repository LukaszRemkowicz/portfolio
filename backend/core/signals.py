from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.ssr_cache import invalidate_frontend_ssr_cache

from .models import LandingPageSettings


@receiver([post_save, post_delete], sender=LandingPageSettings)
def invalidate_settings_ssr_cache(sender, instance, **kwargs):
    transaction.on_commit(lambda: invalidate_frontend_ssr_cache(["settings"]))
