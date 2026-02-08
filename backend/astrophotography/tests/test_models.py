from io import BytesIO
from typing import Any

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import QuerySet
from django.utils.text import slugify

from astrophotography.models import (
    AstroImage,
    Camera,
    Lens,
    MainPageBackgroundImage,
    MainPageLocation,
    Place,
    Tag,
)
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
    TagFactory,
)
from translation.services import TranslationService


@pytest.mark.django_db
class TestAstroImageModel:
    def test_string_representation(self) -> None:
        """Test AstroImage string representation uses the name field"""
        image: AstroImage = AstroImageFactory(name="Test Nebula")
        assert str(image) == "Test Nebula"

    def test_default_ordering(self) -> None:
        """Test default ordering is by created_at descending (from BaseImage)"""
        image1: AstroImage = AstroImageFactory(name="Image 1")
        image2: AstroImage = AstroImageFactory(name="Image 2")
        # Verify ordering (newest first)
        qs: QuerySet[AstroImage] = AstroImage.objects.all()
        assert qs[0] == image2
        assert qs[1] == image1

    def test_thumbnail_generation(self) -> None:
        """Test that a thumbnail is automatically generated on save"""
        image: AstroImage = AstroImageFactory(name="Test Nebula")
        assert image.thumbnail is not None
        assert image.thumbnail.name.startswith("thumbnails/thumb_")

    def test_zoom_field_default(self) -> None:
        """Test that zoom field defaults to False"""
        image: AstroImage = AstroImageFactory()
        assert image.zoom is False

    def test_zoom_field_persistence(self) -> None:
        """Test that zoom field can be set to False and persisted"""
        image: AstroImage = AstroImageFactory(zoom=False)
        assert image.zoom is False
        image.refresh_from_db()
        assert image.zoom is False

    def test_slug_auto_generated(self) -> None:
        """Test that slug is automatically generated from name on creation"""
        name: str = "Nebula in Orion"
        image: AstroImage = AstroImageFactory(name=name, slug=None)
        assert bool(image.slug)
        assert image.slug == slugify(name)

    def test_slug_uniqueness(self) -> None:
        """Test that slugs are unique even if names are identical"""
        name: str = "Same Name"
        image1: AstroImage = AstroImageFactory(name=name)
        image2: AstroImage = AstroImageFactory(name=name)

        assert image1.slug != image2.slug
        assert slugify(name) in image1.slug
        assert slugify(name) in image2.slug


@pytest.mark.django_db
class TestMainPageBackgroundImageModel:
    def test_string_representation(self) -> None:
        """Test MainPageBackgroundImage string representation"""
        bg: MainPageBackgroundImage = MainPageBackgroundImageFactory(name="Test BG")
        assert str(bg) == "Test BG"

    def test_model_creation_and_translation(self) -> None:
        """Verify that MainPageBackgroundImage can be created with translations."""
        img: Image.Image = Image.new("RGB", (1, 1), color="red")
        img_io: BytesIO = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        image_file: SimpleUploadedFile = SimpleUploadedFile(
            "test_bg.png", img_io.read(), content_type="image/png"
        )

        bg_image: MainPageBackgroundImage = MainPageBackgroundImage.objects.create(path=image_file)

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
        place: Place = PlaceFactory(name="Tenerife")
        assert str(place) == "Tenerife"


@pytest.mark.django_db
class TestCameraModel:
    def test_camera_str_method(self) -> None:
        camera: Camera = Camera.objects.create(model="Test Camera Z6")
        assert str(camera) == "Test Camera Z6"


@pytest.mark.django_db
class TestLensModel:
    def test_lens_str_method(self) -> None:
        lens: Lens = Lens.objects.create(model="Nikkor Z 20mm f/1.8")
        assert str(lens) == "Nikkor Z 20mm f/1.8"


@pytest.mark.django_db
class TestMainPageLocationModel:
    def test_string_representation(self) -> None:
        place: Place = PlaceFactory(name="Bieszczady", country="PL")
        slider: MainPageLocation = MainPageLocationFactory(place=place)
        assert str(slider) == "Poland - Bieszczady (Active)"

    def test_string_representation_with_highlight_name(self) -> None:
        slider: MainPageLocation = MainPageLocationFactory(highlight_name="Magical Poland")
        assert str(slider) == "Magical Poland (Active)"

    def test_clean_method_validation_success(self) -> None:
        # Place for PL
        place: Place = PlaceFactory(country="PL")
        # Slider for PL
        slider: MainPageLocation = MainPageLocationFactory(place=place)
        # Image in PL
        image: AstroImage = AstroImageFactory(place=place)

        # Should not raise validation error
        slider.images.add(image)
        slider.clean()


@pytest.mark.django_db
class TestTagModel:
    def test_tag_creation_generates_slug(self) -> None:
        tag: Tag = TagFactory(name="Deep Sky")
        assert tag.slug == "deep-sky"

    def test_tag_translation_access(self) -> None:
        """
        Verify correct translation behavior for the 'name' field.
        """
        tag: Tag = TagFactory(name="Stars")

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

    def test_translation_service_integration(self, mocker: MockerFixture) -> None:
        """
        Verify TranslationService.translate_parler_tag works with the new field structure.
        Only generates name via GPT, slug is synced locally.
        """
        tag: Tag = TagFactory(name="Nebula")  # slug is "nebula"

        # Mock the agent to avoid actual GPT calls
        mock_agent: Any = mocker.Mock()
        mock_agent.translate_tag.side_effect = lambda text, lang: f"TR_{text}"

        mocker.patch.object(TranslationService, "_get_agent", return_value=mock_agent)

        # Execute service method
        TranslationService.translate_parler_tag(tag, "pl")

        # Verify results in DB
        tag.refresh_from_db()
        saved_name: str | None = tag.safe_translation_getter("name", language_code="pl")
        saved_slug: str | None = tag.safe_translation_getter("slug", language_code="pl")

        assert saved_name == "TR_Nebula"
        # Slug is generated from translated name ("TR_Nebula") -> "tr_nebula"
        assert saved_slug == "tr_nebula"
