import factory
from factory.django import DjangoModelFactory

from astrophotography.tests.factories import MeteorsMainPageConfigFactory
from core.models import LandingPageSettings


class LandingPageSettingsFactory(DjangoModelFactory):
    class Meta:
        model = LandingPageSettings
        django_get_or_create = ("pk",)

    contact_form_enabled = True
    travel_highlights_enabled = True
    programming_enabled = True
    lastimages_enabled = True
    meteors = factory.SubFactory(MeteorsMainPageConfigFactory)
    pk = 1


class TranslationTaskFactory(DjangoModelFactory):
    class Meta:
        model = "core.TranslationTask"

    task_id = factory.Faker("uuid4")
    language = "pl"
    method = "translate_method"
    status = "PENDING"
