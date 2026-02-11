from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AstrophotographyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "astrophotography"
    verbose_name = _("Astrophotography")

    def ready(self):
        import astrophotography.signals  # noqa
