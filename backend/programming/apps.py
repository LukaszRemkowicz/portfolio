from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProgrammingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "programming"
    verbose_name = _("Programming")
