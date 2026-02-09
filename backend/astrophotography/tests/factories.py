from collections.abc import Iterable
from typing import Optional

import factory
from factory.django import DjangoModelFactory

from django.utils import timezone

from astrophotography.models import (
    AstroImage,
    Camera,
    Lens,
    MainPageBackgroundImage,
    MeteorsMainPageConfig,
    Tag,
    Telescope,
    Tracker,
    Tripod,
)


class PlaceFactory(DjangoModelFactory):
    class Meta:
        model = "astrophotography.Place"

    name = factory.Faker("city")
    country = "PL"


class AstroImageFactory(DjangoModelFactory):
    class Meta:
        model = AstroImage
        skip_postgeneration_save = True

    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("paragraph")
    path = factory.django.ImageField()
    capture_date = factory.LazyFunction(lambda: timezone.now().date())
    place = factory.SubFactory(PlaceFactory)
    exposure_details = "60x300s, Gain 100"
    processing_details = "PixInsight, BlurXTerminator"
    celestial_object = "Deep Sky"
    astrobin_url = factory.Faker("url")

    @factory.post_generation
    def camera(self, create: bool, extracted: Optional[Iterable[Camera]], **kwargs: dict) -> None:
        if not create:
            return
        if extracted:
            for cam in extracted:
                self.camera.add(cam)

    @factory.post_generation
    def lens(self, create: bool, extracted: Optional[Iterable[Lens]], **kwargs: dict) -> None:
        if not create:
            return
        if extracted:
            for lens_obj in extracted:
                self.lens.add(lens_obj)

    @factory.post_generation
    def telescope(
        self, create: bool, extracted: Optional[Iterable[Telescope]], **kwargs: dict
    ) -> None:
        if not create:
            return
        if extracted:
            for tele in extracted:
                self.telescope.add(tele)

    @factory.post_generation
    def tracker(self, create: bool, extracted: Optional[Iterable[Tracker]], **kwargs: dict) -> None:
        if not create:
            return
        if extracted:
            for track in extracted:
                self.tracker.add(track)

    @factory.post_generation
    def tripod(self, create: bool, extracted: Optional[Iterable[Tripod]], **kwargs: dict) -> None:
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

    model = factory.Faker("word")


class TripodFactory(DjangoModelFactory):
    class Meta:
        model = Tripod

    model = factory.Faker("word")


class MainPageLocationFactory(DjangoModelFactory):
    class Meta:
        model = "astrophotography.MainPageLocation"
        skip_postgeneration_save = True

    place = factory.SubFactory(PlaceFactory)
    highlight_name = factory.Faker("city")
    is_active = True

    @factory.post_generation
    def images(
        self, create: bool, extracted: Optional[Iterable[AstroImage]], **kwargs: dict
    ) -> None:
        if not create:
            return
        if extracted:
            for image in extracted:
                self.images.add(image)


class MeteorsMainPageConfigFactory(DjangoModelFactory):
    class Meta:
        model = MeteorsMainPageConfig

    random_stars_shooting = True
    bolid_chance = 0.1
    bolid_interval = 60.0
    star_path_range = [50, 500]
    bolid_path_range = [50, 500]
    star_streak_range = [100, 200]
    star_opacity_range = [0.4, 0.8]
    bolid_opacity_range = [0.7, 1.0]
    smoke_opacity_range = [0.5, 0.8]


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker("word")
