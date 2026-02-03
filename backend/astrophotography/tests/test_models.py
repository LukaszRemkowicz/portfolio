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

    def test_slug_auto_generated(self):
        """Test that slug is automatically generated from name on creation"""
        from django.utils.text import slugify

        name = "Nebula in Orion"
        image = AstroImageFactory(name=name, slug=None)
        assert bool(image.slug)
        assert image.slug == slugify(name)

    def test_slug_uniqueness(self):
        """Test that slugs are unique even if names are identical"""
        from django.utils.text import slugify

        name = "Same Name"
        image1 = AstroImageFactory(name=name)
        image2 = AstroImageFactory(name=name)

        assert image1.slug != image2.slug
        assert slugify(name) in image1.slug
        assert slugify(name) in image2.slug


@pytest.mark.django_db
class TestMainPageBackgroundImageModel:
    def test_string_representation(self):
        """Test MainPageBackgroundImage string representation"""
        bg = MainPageBackgroundImageFactory(name="Test BG")
        assert str(bg) == "Test BG"

    def test_model_creation_and_translation(self):
        """Verify that MainPageBackgroundImage can be created with translations."""
        from io import BytesIO

        from PIL import Image

        from django.core.files.uploadedfile import SimpleUploadedFile

        img = Image.new("RGB", (1, 1), color="red")
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        image_file = SimpleUploadedFile("test_bg.png", img_io.read(), content_type="image/png")

        from astrophotography.models import MainPageBackgroundImage

        bg_image = MainPageBackgroundImage.objects.create(path=image_file)

        bg_image.set_current_language("en")
        bg_image.name = "Test Background"
        bg_image.save()

        bg_image.set_current_language("pl")
        bg_image.name = "Testowe Tło"
        bg_image.save()

        bg_image.refresh_from_db()

        bg_image.set_current_language("en")
        assert bg_image.name == "Test Background"

        bg_image.set_current_language("pl")
        assert bg_image.name == "Testowe Tło"


@pytest.mark.django_db
class TestPlaceModel:
    def test_string_representation(self):
        place = PlaceFactory(name="Tenerife")
        assert str(place) == "Tenerife"


@pytest.mark.django_db
class TestCameraModel:
    def test_camera_str_method(self):
        from astrophotography.models import Camera

        camera = Camera.objects.create(model="Test Camera Z6")
        assert str(camera) == "Test Camera Z6"


@pytest.mark.django_db
class TestLensModel:
    def test_lens_str_method(self):
        from astrophotography.models import Lens

        lens = Lens.objects.create(model="Nikkor Z 20mm f/1.8")
        assert str(lens) == "Nikkor Z 20mm f/1.8"


@pytest.mark.django_db
class TestMainPageLocationModel:
    def test_string_representation(self):
        place = PlaceFactory(name="Bieszczady", country="PL")
        slider = MainPageLocationFactory(place=place)
        assert str(slider) == "Poland - Bieszczady (Active)"

    def test_string_representation_with_highlight_name(self):
        slider = MainPageLocationFactory(highlight_name="Magical Poland")
        assert str(slider) == "Magical Poland (Active)"

    def test_clean_method_validation_success(self):
        # Place for PL
        place = PlaceFactory(country="PL")
        # Slider for PL
        slider = MainPageLocationFactory(place=place)
        # Image in PL
        image = AstroImageFactory(place=place)

        # Should not raise validation error
        slider.images.add(image)
        slider.clean()
