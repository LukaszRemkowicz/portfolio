from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InboxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inbox"
    verbose_name = _("Inbox")
