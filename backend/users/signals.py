# users/signals.py

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService

from .models import Profile

User = get_user_model()


@receiver([post_save, post_delete], sender=User)
@receiver([post_save, post_delete], sender="users.UserTranslation")
def invalidate_user_cache(sender, instance, **kwargs):
    CacheService.invalidate_user_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["profile"])


@receiver([post_save, post_delete], sender=Profile)
@receiver([post_save, post_delete], sender="users.ProfileTranslation")
def invalidate_profile_cache(sender, instance, **kwargs):
    CacheService.invalidate_user_cache()
    invalidate_frontend_ssr_cache_task.delay_on_commit(["profile"])
