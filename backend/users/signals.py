# users/signals.py

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.ssr_cache import invalidate_frontend_ssr_cache
from core.cache_service import CacheService

from .models import Profile

User = get_user_model()


@receiver([post_save, post_delete], sender=User)
@receiver([post_save, post_delete], sender="users.UserTranslation")
def invalidate_user_cache(sender, instance, **kwargs):
    CacheService.invalidate_user_cache()
    transaction.on_commit(lambda: invalidate_frontend_ssr_cache(["profile"]))


@receiver([post_save, post_delete], sender=Profile)
@receiver([post_save, post_delete], sender="users.ProfileTranslation")
def invalidate_profile_cache(sender, instance, **kwargs):
    CacheService.invalidate_user_cache()
    transaction.on_commit(lambda: invalidate_frontend_ssr_cache(["profile"]))
