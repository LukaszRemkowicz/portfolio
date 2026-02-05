# backend/astrophotography/tests/test_models.py
import pytest
from _pytest.monkeypatch import MonkeyPatch

from astrophotography.models import AstroImage
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
    TagFactory,
)
from core.services import TranslationService


@pytest.mark.django_db
class TestAstroImageModel:
    def test_string_representation(self) -> None:
        """Test AstroImage string representation uses the name field"""
        image = AstroImageFactory(name="Test Nebula")
        assert str(image) == f"Test Nebula ({image.capture_date})"

    def test_default_ordering(self) -> None:
        """Test default ordering is by created_at descending (from BaseImage)"""
        image1 = AstroImageFactory(name="Image 1")
        image2 = AstroImageFactory(name="Image 2")
        # Verify ordering (newest first)
        qs = AstroImage.objects.all()
        assert qs[0] == image2
        assert qs[1] == image1

    def test_thumbnail_generation(self) -> None:
        """Test that a thumbnail is automatically generated on save"""
        image = AstroImageFactory(name="Test Nebula")
        assert image.thumbnail is not None
        assert image.thumbnail.name.startswith("thumbnails/thumb_")

    def test_zoom_field_default(self) -> None:
        """Test that zoom field defaults to False"""
        image = AstroImageFactory()
        assert image.zoom is False

    def test_zoom_field_persistence(self) -> None:
        """Test that zoom field can be set to False and persisted"""
        image = AstroImageFactory(zoom=False)
        assert image.zoom is False
        image.refresh_from_db()
        assert image.zoom is False

    def test_slug_auto_generated(self) -> None:
        """Test that slug is automatically generated from name on creation"""
        from django.utils.text import slugify

        name = "Nebula in Orion"
        image = AstroImageFactory(name=name, slug=None)
        assert bool(image.slug)
        assert image.slug == slugify(name)

    def test_slug_uniqueness(self) -> None:
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
    def test_string_representation(self) -> None:
        """Test MainPageBackgroundImage string representation"""
        bg = MainPageBackgroundImageFactory(name="Test BG")
        assert str(bg) == "Test BG"

    def test_model_creation_and_translation(self) -> None:
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
    def test_string_representation(self) -> None:
        place = PlaceFactory(name="Tenerife")
        assert str(place) == "Tenerife"


@pytest.mark.django_db
class TestCameraModel:
    def test_camera_str_method(self) -> None:
        from astrophotography.models import Camera

        camera = Camera.objects.create(model="Test Camera Z6")
        assert str(camera) == "Test Camera Z6"


@pytest.mark.django_db
class TestLensModel:
    def test_lens_str_method(self) -> None:
        from astrophotography.models import Lens

        lens = Lens.objects.create(model="Nikkor Z 20mm f/1.8")
        assert str(lens) == "Nikkor Z 20mm f/1.8"


@pytest.mark.django_db
class TestMainPageLocationModel:
    def test_string_representation(self) -> None:
        place = PlaceFactory(name="Bieszczady", country="PL")
        slider = MainPageLocationFactory(place=place)
        assert str(slider) == "Poland - Bieszczady (Active)"

    def test_string_representation_with_highlight_name(self) -> None:
        slider = MainPageLocationFactory(highlight_name="Magical Poland")
        assert str(slider) == "Magical Poland (Active)"

    def test_clean_method_validation_success(self) -> None:
        # Place for PL
        place = PlaceFactory(country="PL")
        # Slider for PL
        slider = MainPageLocationFactory(place=place)
        # Image in PL
        image = AstroImageFactory(place=place)

        # Should not raise validation error
        slider.images.add(image)
        slider.clean()


@pytest.mark.django_db
class TestTagModel:
    def test_tag_creation_generates_slug(self) -> None:
        tag = TagFactory(name="Deep Sky")
        assert tag.slug == "deep-sky"

    def test_tag_translation_access(self) -> None:
        """
        Verify correct translation behavior for the 'name' field.
        """
        tag = TagFactory(name="Stars")

        # Add Polish translation
        tag.set_current_language("pl")
        tag.name = "Gwiazdy"
        tag.save()

        # Verify English
        tag.set_current_language("en")
        assert tag.name == "Stars"

        # Verify Polish
        tag.set_current_language("pl")
        assert tag.name == "Gwiazdy"

        # Verify direct getter
        assert tag.safe_translation_getter("name", language_code="en") == "Stars"
        assert tag.safe_translation_getter("name", language_code="pl") == "Gwiazdy"

    def test_translation_service_integration(self, monkeypatch: MonkeyPatch) -> None:
        """
        Verify TranslationService.translate_parler_tag works with the new field structure.
        Only generates name via GPT, slug is synced locally.
        """
        tag = TagFactory(name="Nebula")  # slug is "nebula"

        # Mock the agent to avoid actual GPT calls
        def mock_translate_tag(text, lang):
            return f"TR_{text}"

        monkeypatch.setattr(TranslationService.agent, "translate_tag", mock_translate_tag)

        # Execute service method
        TranslationService.translate_parler_tag(tag, "pl")

        # Verify results in DB
        tag.refresh_from_db()
        saved_name = tag.safe_translation_getter("name", language_code="pl")
        saved_slug = tag.safe_translation_getter("slug", language_code="pl")

        assert saved_name == "TR_Nebula"
        # Slug is generated from translated name ("TR_Nebula") -> "tr_nebula"
        assert saved_slug == "tr_nebula"
