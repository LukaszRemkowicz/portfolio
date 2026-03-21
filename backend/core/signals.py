from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.tasks import invalidate_frontend_ssr_cache_task

from .models import LandingPageSettings


@receiver([post_save, post_delete], sender=LandingPageSettings)
def invalidate_settings_ssr_cache(sender, instance, **kwargs):
    invalidate_frontend_ssr_cache_task.delay_on_commit(["settings"])
