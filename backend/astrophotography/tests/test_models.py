# backend/astrophotography/tests/test_models.py
import pytest

from astrophotography.models import AstroImage
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
)


@pytest.mark.django_db
class TestAstroImageModel:
    def test_string_representation(self):
        """Test AstroImage string representation uses the name field"""
        image = AstroImageFactory(name="Test Nebula")
        assert str(image) == f"Test Nebula ({image.capture_date})"

    def test_default_ordering(self):
        """Test default ordering is by created_at descending (from BaseImage)"""
        image1 = AstroImageFactory(name="Image 1")
        image2 = AstroImageFactory(name="Image 2")
        # Verify ordering (newest first)
        qs = AstroImage.objects.all()
        assert qs[0] == image2
        assert qs[1] == image1

    def test_thumbnail_generation(self):
        """Test that a thumbnail is automatically generated on save"""
        image = AstroImageFactory(name="Test Nebula")
        assert image.thumbnail is not None
        assert image.thumbnail.name.startswith("thumbnails/thumb_")

    def test_zoom_field_default(self):
        """Test that zoom field defaults to False"""
        image = AstroImageFactory()
        assert image.zoom is False

    def test_zoom_field_persistence(self):
        """Test that zoom field can be set to False and persisted"""
        image = AstroImageFactory(zoom=False)
        assert image.zoom is False
        image.refresh_from_db()
        assert image.zoom is False


@pytest.mark.django_db
class TestMainPageBackgroundImageModel:
    def test_string_representation(self):
        """Test MainPageBackgroundImage string representation"""
        bg = MainPageBackgroundImageFactory()
        assert str(bg) == bg.name


@pytest.mark.django_db
class TestPlaceModel:
    def test_string_representation(self):
        place = PlaceFactory(name="Tenerife")
        assert str(place) == "Tenerife"


@pytest.mark.django_db
class TestMainPageLocationModel:
    def test_string_representation(self):
        slider = MainPageLocationFactory(country="PL", place__name="Bieszczady")
        assert str(slider) == "Location: Poland (Bieszczady) (Active)"

    def test_string_representation_with_highlight_name(self):
        slider = MainPageLocationFactory(highlight_name="Magical Poland")
        assert str(slider) == "Magical Poland (Active)"

    def test_clean_method_validation_success(self):
        # Slider for PL
        slider = MainPageLocationFactory(country="PL")
        # Image in PL
        image = AstroImageFactory(location="PL")

        # Should not raise validation error
        slider.images.add(image)
        slider.clean()
