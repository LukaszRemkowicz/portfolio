from datetime import date
from io import BytesIO
from typing import Any

import pytest
from PIL import Image
from psycopg2.extras import DateRange
from pytest_mock import MockerFixture

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.db.models import QuerySet
from django.utils.text import slugify

from astrophotography.forms import AstroImageForm
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
from core.models import LandingPageSettings
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
        image.refresh_from_db()
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

    def test_get_thumbnail_url_with_image(self) -> None:
        """
        Verify that get_thumbnail_url returns a valid URL when an image exists.
        This tests the inherited logic from BaseImage.
        """
        image: AstroImage = AstroImageFactory()
        image.refresh_from_db()
        url: str = image.get_thumbnail_url()
        assert url
        assert "/media/thumbnails/" in url or "/media/images/" in url

    def test_get_thumbnail_url_returns_none_when_thumbnail_file_missing(self) -> None:
        """Missing thumbnail files should not leak dead media URLs to the API."""
        image: AstroImage = AstroImageFactory()
        image.refresh_from_db()

        assert image.thumbnail is not None

        missing_name = str(image.thumbnail.name)
        image.thumbnail.storage.delete(missing_name)

        assert image.get_thumbnail_url() is None

    def test_get_path_spec(self):
        """Test that get_path_spec returns correct spec based on webp_quality."""
        # Quality >= 90 -> LANDSCAPE
        image_l: AstroImage = AstroImageFactory()
        image_l.webp_quality = 90
        spec_l = image_l.get_path_spec()
        assert spec_l == settings.IMAGE_OPTIMIZATION_SPECS["LANDSCAPE"]

        # Quality < 90 -> PORTRAIT
        image_p: AstroImage = AstroImageFactory()
        image_p.webp_quality = 80
        spec_p = image_p.get_path_spec()
        assert spec_p == settings.IMAGE_OPTIMIZATION_SPECS["PORTRAIT"]


@pytest.mark.django_db
class TestMainPageBackgroundImageModel:
    def test_string_representation(self) -> None:
        """Test MainPageBackgroundImage string representation"""
        bg: MainPageBackgroundImage = MainPageBackgroundImageFactory(name="Test BG")
        assert str(bg) == "Test BG"

    def test_get_path_spec_uses_background_specific_settings(self) -> None:
        """Backgrounds should use their own quality/dimension, not generic image buckets."""
        bg: MainPageBackgroundImage = MainPageBackgroundImageFactory(name="Test BG")
        spec = bg.get_path_spec()
        assert spec.dimension == bg.max_dimension
        assert spec.quality == bg.webp_quality

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

    def test_can_create_multiple_nameless_places(self) -> None:
        """Verify that multiple places without names can coexist."""
        p1 = Place.objects.create(country="PL")
        p2 = Place.objects.create(country="FI")
        assert p1.pk != p2.pk
        assert (p1.safe_translation_getter("name", any_language=True) or "") == ""
        assert (p2.safe_translation_getter("name", any_language=True) or "") == ""

    def test_duplicate_name_same_language_failure(self) -> None:
        """Verify that duplicate names in the same language raise ValidationError."""
        Place.objects.create(name="Duplicate", country="PL")
        p2 = Place(name="Duplicate", country="FI")
        with pytest.raises(ValidationError) as exc:
            p2.clean()
        assert "Place Translation with this Language and Name already exists" in str(exc.value)

    def test_duplicate_name_different_language_success(self) -> None:
        """Verify that the same name can exist in different languages."""
        Place.objects.create(name="Home", country="PL")

        # Create another place and set its name to 'Home' in Polish
        p2 = Place.objects.create(country="FI")
        p2.set_current_language("pl")
        p2.name = "Home"
        # Should not raise any error
        p2.clean()
        p2.save()

        assert Place.objects.translated("en", name="Home").count() == 1
        assert Place.objects.translated("pl", name="Home").count() == 1

    def test_updating_own_name_success(self) -> None:
        """Verify that updating an existing record with its own name works."""
        place = Place.objects.create(name="Unique", country="PL")
        place.clean()  # Should not raise
        place.save()


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
        slider: MainPageLocation = MainPageLocationFactory(place=place, highlight_name=None)
        assert str(slider) == "Poland - Bieszczady (Active)"

    def test_string_representation_with_highlight_name(self) -> None:
        slider: MainPageLocation = MainPageLocationFactory(highlight_name="Magical Poland")
        assert str(slider) == "Magical Poland (Active)"

    def test_clean_method_validation_success(self) -> None:
        # Place for PL
        place: Place = PlaceFactory(country="PL")
        # Slider for PL
        slider: MainPageLocation = MainPageLocationFactory(place=place, highlight_name="Test")
        # Image in PL
        image: AstroImage = AstroImageFactory(place=place)

        # Should not raise validation error
        slider.images.add(image)
        slider.clean()

    def test_overlapping_date_range_validation_failure(self) -> None:
        place: Place = PlaceFactory(country="PL")
        # 2025-01-01 to 2025-01-10
        date_range1 = DateRange(date(2025, 1, 1), date(2025, 1, 10))
        # 2025-01-05 to 2025-01-15 (Overlaps!)
        date_range2 = DateRange(date(2025, 1, 5), date(2025, 1, 15))

        # First location succeeds
        MainPageLocationFactory(place=place, adventure_date=date_range1)

        # Second location with overlapping date should fail DB-level enforcement
        # Note: Python-level clean() check was removed as redundant with DB constraint.
        with pytest.raises(IntegrityError):
            MainPageLocationFactory(place=place, adventure_date=date_range2)

    def test_disjoint_date_ranges_succeed(self) -> None:
        place: Place = PlaceFactory(country="PL")
        date_range1 = DateRange(date(2025, 1, 1), date(2025, 1, 10))
        date_range2 = DateRange(date(2025, 1, 11), date(2025, 1, 20))

        MainPageLocationFactory(place=place, adventure_date=date_range1)
        # Should NOT raise any error
        MainPageLocationFactory(place=place, adventure_date=date_range2)


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

        # Instantiate service with mock agent
        service = TranslationService(agent=mock_agent)

        # Execute service instance method
        service.translate_parler_tag(tag, "pl")

        # Verify results in DB
        tag.refresh_from_db()
        saved_name: str | None = tag.safe_translation_getter("name", language_code="pl")
        saved_slug: str | None = tag.safe_translation_getter("slug", language_code="pl")

        assert saved_name == "TR_Nebula"
        # Slug is generated from translated name ("TR_Nebula") -> "tr_nebula"
        assert saved_slug == "tr_nebula"


@pytest.mark.django_db
class TestImageUpdateLogic:
    def test_thumbnail_updates_when_image_changes(self) -> None:
        """
        Verify that the thumbnail is regenerated when the path (image file) changes.
        """
        # 1. Create initial image
        img_data1 = BytesIO()
        Image.new("RGB", (100, 100), color="red").save(img_data1, "JPEG")
        file1 = SimpleUploadedFile("shared.jpg", img_data1.getvalue(), content_type="image/jpeg")

        image: AstroImage = AstroImageFactory(path=file1)
        image.refresh_from_db()
        initial_thumb_name = image.thumbnail.name
        initial_thumb_content = image.thumbnail.read()

        # 2. Update with NEW image but SAME filename
        img_data2 = BytesIO()
        Image.new("RGB", (100, 100), color="blue").save(img_data2, "JPEG")
        file2 = SimpleUploadedFile("shared.jpg", img_data2.getvalue(), content_type="image/jpeg")

        image.path = file2
        image.save()

        image.refresh_from_db()

        # 3. Assertions
        new_thumb_content = image.thumbnail.read()
        assert new_thumb_content != initial_thumb_content, (
            f"Thumbnail content should change! \n"
            f"Initial thumb: {initial_thumb_name}\n"
            f"New thumb: {image.thumbnail.name}"
        )

    def test_thumbnail_does_not_update_when_image_is_same(self) -> None:
        """
        Verify that the thumbnail is NOT regenerated if we save without changing the image.
        """
        image: AstroImage = AstroImageFactory(name="Stationary Image")
        image.refresh_from_db()
        initial_thumb_name = image.thumbnail.name

        # Save again without changing path
        image.save()

        image.refresh_from_db()
        assert (
            image.thumbnail.name == initial_thumb_name
        ), "Thumbnail should NOT have been regenerated"

    def test_update_via_form(self) -> None:
        """
        Simulate a Django Admin update using the actual model form.
        """
        # 1. Create initial
        image: AstroImage = AstroImageFactory(name="Form Test")
        old_path = image.path.name
        old_thumb_name = image.thumbnail.name

        # 2. Prepare form data with NEW image
        img_data = BytesIO()
        Image.new("RGB", (100, 100), color="green").save(img_data, "JPEG")
        new_file = SimpleUploadedFile(
            "new_image.jpg", img_data.getvalue(), content_type="image/jpeg"
        )

        # In Django Admin, we'd have name, description, etc.
        data = {
            "name": "Updated Name",
            "capture_date": "2024-01-01",
            "celestial_object": "Landscape",
        }
        files = {"path": new_file}

        form = AstroImageForm(data=data, files=files, instance=image)
        if not form.is_valid():
            print(f"DEBUG Form errors: {form.errors}")
        assert form.is_valid()

        # 3. Save via form
        form.save()

        image.refresh_from_db()
        assert image.path.name != old_path
        assert image.thumbnail.name != old_thumb_name
        assert image.name == "Updated Name"

    def test_form_hides_internal_calculated_exposure_hours_field(self) -> None:
        """Admin form should not expose internal derived exposure-hour storage."""
        image: AstroImage = AstroImageFactory(name="Hidden Internal Field Test")

        form = AstroImageForm(instance=image)

        assert "calculated_exposure_hours" not in form.fields

    def test_replacing_existing_image_keeps_new_file_and_removes_old_file(self) -> None:
        """
        Replacing an existing image must not delete the freshly uploaded file.
        Only the previous file should be removed.
        """
        image: AstroImage = AstroImageFactory(name="Replacement Persistence Test")
        image.refresh_from_db()

        old_path = str(image.path.name)
        assert image.path.storage.exists(old_path)

        img_data = BytesIO()
        Image.new("RGB", (100, 100), color="purple").save(img_data, "PNG")
        new_file = SimpleUploadedFile(
            "replacement_persistence.png", img_data.getvalue(), content_type="image/png"
        )

        image.path = new_file
        image.save()
        image.refresh_from_db()

        new_path = str(image.path.name)
        assert new_path != old_path
        assert image.path.storage.exists(new_path)
        assert not image.path.storage.exists(old_path)

    def test_form_is_invalid_when_existing_image_file_is_missing(self) -> None:
        """
        Admin/model forms must reject editing a row whose path points to a missing file.
        """
        image: AstroImage = AstroImageFactory(name="Broken Existing Image")
        image.refresh_from_db()
        image.path.storage.delete(image.path.name)

        data = {
            "name": "Broken Existing Image Updated",
            "capture_date": image.capture_date.isoformat(),
            "celestial_object": image.celestial_object,
        }

        form = AstroImageForm(data=data, instance=image)

        assert not form.is_valid()
        assert "path" in form.errors

    def test_form_allows_replacing_missing_existing_image_with_new_upload(self) -> None:
        """
        Broken existing rows should be repairable through the admin form when
        a new file is uploaded.
        """
        image: AstroImage = AstroImageFactory(name="Broken But Replaceable")
        image.refresh_from_db()
        image.path.storage.delete(image.path.name)

        img_data = BytesIO()
        Image.new("RGB", (100, 100), color="purple").save(img_data, "PNG")
        replacement = SimpleUploadedFile(
            "replacement.png", img_data.getvalue(), content_type="image/png"
        )

        data = {
            "name": "Broken But Replaceable",
            "capture_date": image.capture_date.isoformat(),
            "celestial_object": image.celestial_object,
        }
        files = {"path": replacement}

        form = AstroImageForm(data=data, files=files, instance=image)

        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestTagQuerySet:
    def test_latest_tags_returns_configured_tags(self) -> None:
        """Verify that latest_tags() returns only tags configured in LandingPageSettings."""
        tag1 = TagFactory(name="Tag 1")
        tag2 = TagFactory(name="Tag 2")
        TagFactory(name="Other Tag")

        settings, _ = LandingPageSettings.objects.get_or_create()
        settings.latest_filters.add(tag1, tag2)

        latest = Tag.objects.latest_tags()
        assert latest.count() == 2
        assert tag1 in latest
        assert tag2 in latest

    def test_latest_tags_returns_empty_when_no_settings(self) -> None:
        """Verify that latest_tags() returns empty queryset when no settings are configured."""
        TagFactory(name="Tag 1")
        # Ensure no LandingPageSettings exist
        LandingPageSettings.objects.all().delete()

        latest = Tag.objects.latest_tags()
        assert latest.count() == 0
