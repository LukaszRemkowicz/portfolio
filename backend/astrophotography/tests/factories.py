import factory
from factory.django import DjangoModelFactory

from django.utils import timezone

from astrophotography.models import AstroImage, MainPageBackgroundImage


class AstroImageFactory(DjangoModelFactory):
    class Meta:
        model = AstroImage

    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("paragraph")
    path = factory.django.ImageField()
    capture_date = factory.LazyFunction(lambda: timezone.now().date())
    location = "PL"
    equipment = "EQ6-R, Newton 200/1000, ASI2600MC"
    exposure_details = "60x300s, Gain 100"
    processing_details = "PixInsight, BlurXTerminator"
    celestial_object = "Deep Sky"
    astrobin_url = factory.Faker("url")


class MainPageBackgroundImageFactory(DjangoModelFactory):
    class Meta:
        model = MainPageBackgroundImage

    name = factory.Faker("sentence", nb_words=2)
    path = factory.django.ImageField()


class PlaceFactory(DjangoModelFactory):
    class Meta:
        model = "astrophotography.Place"

    name = factory.Faker("city")


class MainPageLocationSliderFactory(DjangoModelFactory):
    class Meta:
        model = "astrophotography.MainPageLocationSlider"
        skip_postgeneration_save = True

    country = factory.Iterator(["PL", "US", "NO", "CL"])
    place = factory.SubFactory(PlaceFactory)
    highlight_name = None
    is_active = True

    @factory.post_generation
    def images(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for image in extracted:
                self.images.add(image)
