import factory
from factory.django import DjangoModelFactory

from django.contrib.contenttypes.models import ContentType

from astrophotography.tests.factories import MeteorsMainPageConfigFactory
from core.models import ImageVariant, LandingPageSettings


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
        model = "translation.TranslationTask"

    task_id = factory.Faker("uuid4")
    language = "pl"
    method = "translate_method"
    status = "PENDING"


class ImageVariantFactory(DjangoModelFactory):
    class Meta:
        model = ImageVariant
        exclude = ("image",)

    class Params:
        image = factory.SubFactory("astrophotography.tests.factories.AstroImageFactory")

    content_type = factory.LazyAttribute(
        lambda obj: ContentType.objects.get_for_model(obj.image, for_concrete_model=False)
    )
    object_id = factory.LazyAttribute(lambda obj: str(obj.image.pk))
    file = factory.django.FileField(filename="variant.webp", data=b"variant")
    role = "thumbnail"
    width = 560
    height = 373
    mime_type = "image/webp"
