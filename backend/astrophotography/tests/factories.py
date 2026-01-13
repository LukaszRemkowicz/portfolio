import factory
from factory.django import DjangoModelFactory

from django.utils import timezone

from astrophotography.models import AstroImage, BackgroundMainPage


class AstroImageFactory(DjangoModelFactory):
    class Meta:
        model = AstroImage

    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("paragraph")
    path = factory.Faker("file_name", extension="jpg")
    capture_date = factory.LazyFunction(lambda: timezone.now().date())
    location = "Dark Site, Poland"
    equipment = "EQ6-R, Newton 200/1000, ASI2600MC"
    exposure_details = "60x300s, Gain 100"
    processing_details = "PixInsight, BlurXTerminator"
    celestial_object = "Deep Sky"
    astrobin_url = factory.Faker("url")


class BackgroundMainPageFactory(DjangoModelFactory):
    class Meta:
        model = BackgroundMainPage

    image = factory.django.ImageField()
