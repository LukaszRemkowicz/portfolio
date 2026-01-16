from factory.django import DjangoModelFactory

from core.models import LandingPageSettings


class LandingPageSettingsFactory(DjangoModelFactory):
    class Meta:
        model = LandingPageSettings
        django_get_or_create = ("pk",)

    contact_form_enabled = True
    location_slider_enabled = True
    programming_enabled = True
    pk = 1
