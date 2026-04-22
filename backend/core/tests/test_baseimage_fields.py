import pytest

from astrophotography.models import AstroImage, MainPageBackgroundImage
from astrophotography.tests.factories import MainPageBackgroundImageFactory
from programming.models import ProjectImage


@pytest.mark.django_db
class TestBaseImageFields:
    def test_new_fields_exist_on_all_baseimage_models(self) -> None:
        for model in (AstroImage, MainPageBackgroundImage, ProjectImage):
            assert model._meta.get_field("original")
            assert model._meta.get_field("original_webp")

    def test_accessors_return_canonical_new_fields(self) -> None:
        image = MainPageBackgroundImageFactory()
        image.original = "images/new-original.jpg"
        image.original_webp = "images/new-original.webp"
        image.original_image = "images/legacy-original.jpg"
        image.path = "images/legacy-derived.webp"

        assert image.original_field.name == "images/new-original.jpg"
        assert image.original_webp_field.name == "images/new-original.webp"

    def test_original_field_returns_canonical_source_field(self) -> None:
        image = MainPageBackgroundImageFactory.build()
        image.original = "images/pending-upload.jpg"
        image.path = "images/legacy-mirror.jpg"

        assert image.original_field.name == "images/pending-upload.jpg"
