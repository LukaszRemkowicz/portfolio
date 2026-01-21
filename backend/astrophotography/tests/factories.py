import factory
from factory.django import DjangoModelFactory

from django.utils import timezone

from astrophotography.models import (
    AstroImage,
    Camera,
    Lens,
    MainPageBackgroundImage,
    Telescope,
    Tracker,
    Tripod,
)


class AstroImageFactory(DjangoModelFactory):
    class Meta:
        model = AstroImage
        skip_postgeneration_save = True

    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("paragraph")
    path = factory.django.ImageField()
    capture_date = factory.LazyFunction(lambda: timezone.now().date())
    location = "PL"
    exposure_details = "60x300s, Gain 100"
    processing_details = "PixInsight, BlurXTerminator"
    celestial_object = "Deep Sky"
    astrobin_url = factory.Faker("url")

    @factory.post_generation
    def camera(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for cam in extracted:
                self.camera.add(cam)

    @factory.post_generation
    def lens(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for lens_obj in extracted:
                self.lens.add(lens_obj)

    @factory.post_generation
    def telescope(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tele in extracted:
                self.telescope.add(tele)

    @factory.post_generation
    def tracker(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for track in extracted:
                self.tracker.add(track)

    @factory.post_generation
    def tripod(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tri in extracted:
                self.tripod.add(tri)


class MainPageBackgroundImageFactory(DjangoModelFactory):
    class Meta:
        model = MainPageBackgroundImage

    name = factory.Faker("sentence", nb_words=2)
    path = factory.django.ImageField()


class CameraFactory(DjangoModelFactory):
    class Meta:
        model = Camera

    model = factory.Faker("word")


class LensFactory(DjangoModelFactory):
    class Meta:
        model = Lens

    model = factory.Faker("word")


class TelescopeFactory(DjangoModelFactory):
    class Meta:
        model = Telescope

    model = factory.Faker("word")


class TrackerFactory(DjangoModelFactory):
    class Meta:
        model = Tracker

    name = factory.Faker("word")


class TripodFactory(DjangoModelFactory):
    class Meta:
        model = Tripod

    name = factory.Faker("word")


class PlaceFactory(DjangoModelFactory):
    class Meta:
        model = "astrophotography.Place"

    name = factory.Faker("city")


class MainPageLocationFactory(DjangoModelFactory):
    class Meta:
        model = "astrophotography.MainPageLocation"
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
