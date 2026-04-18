import pytest

from astrophotography.models import AstroImage, MainPageBackgroundImage
from astrophotography.tests.factories import MainPageBackgroundImageFactory
from programming.models import ProjectImage


@pytest.mark.django_db
class TestBaseImagePhase2Fields:
    def test_new_fields_exist_on_all_baseimage_models(self) -> None:
        for model in (AstroImage, MainPageBackgroundImage, ProjectImage):
            assert model._meta.get_field("original")
            assert model._meta.get_field("original_webp")

    def test_compatibility_accessors_prefer_new_fields(self) -> None:
        image = MainPageBackgroundImageFactory()
        image.original = "images/new-original.jpg"
        image.original_webp = "images/new-original.webp"
        image.original_image = "images/legacy-original.jpg"
        image.path = "images/legacy-derived.webp"

        assert image.get_original_field().name == "images/new-original.jpg"
        assert image.get_original_webp_field().name == "images/new-original.webp"

    def test_compatibility_accessors_fall_back_to_legacy_fields(self) -> None:
        image = MainPageBackgroundImageFactory()
        image.original = None
        image.original_webp = None
        image.original_image = "images/legacy-original.jpg"
        image.path = "images/legacy-derived.webp"

        assert image.get_original_field().name == "images/legacy-original.jpg"
        assert image.get_original_webp_field().name == "images/legacy-derived.webp"
