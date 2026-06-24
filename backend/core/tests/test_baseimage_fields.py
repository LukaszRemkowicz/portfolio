import pytest

from django.core.exceptions import FieldDoesNotExist

from astrophotography.models import AstroImage, MainPageBackgroundImage
from astrophotography.tests.factories import MainPageBackgroundImageFactory
from programming.models import ProjectImage


@pytest.mark.django_db
class TestBaseImageFields:
    def test_canonical_fields_exist_on_all_baseimage_models(self) -> None:
        for model in (AstroImage, MainPageBackgroundImage, ProjectImage):
            assert model._meta.get_field("original")
            with pytest.raises(FieldDoesNotExist):
                model._meta.get_field("original_webp")

    def test_accessors_return_canonical_source_field(self) -> None:
        image = MainPageBackgroundImageFactory()
        image.original = "images/new-original.jpg"

        assert image.original.name == "images/new-original.jpg"

    def test_original_field_returns_canonical_source_field(self) -> None:
        image = MainPageBackgroundImageFactory.build()
        image.original = "images/pending-upload.jpg"

        assert image.original.name == "images/pending-upload.jpg"
