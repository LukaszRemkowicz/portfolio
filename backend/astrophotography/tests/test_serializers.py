from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from psycopg2.extras import DateRange
from pytest_mock import MockerFixture

from astrophotography.models import Tag
from astrophotography.serializers import (
    AstroImageDetailSerializer,
    AstroImageSerializer,
    MainPageBackgroundImageSerializer,
    MainPageLocationSerializer,
    MeteorsMainPageConfigSerializer,
    PlaceSerializer,
    TagSerializer,
)
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
)
from common.tests.image_helpers import jpeg_field
from core.tasks import process_image_task
from core.tests.factories import ImageVariantFactory


@pytest.mark.django_db
class TestEquipmentSerializers:

    def test_place_serializer_configuration(self) -> None:

        try:
            serializer = PlaceSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"PlaceSerializer Configuration Error: {e}")

    def test_meteors_config_serializer_configuration(self) -> None:

        try:
            # Should have explicit fields
            serializer = MeteorsMainPageConfigSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"MeteorsMainPageConfigSerializer Configuration Error: {e}")

    def test_astro_image_serializer_configuration(self) -> None:

        try:
            serializer = AstroImageSerializer()
            # This will trigger field inspection for nested serializers too
            _ = serializer.fields
        except AssertionError as e:
            # If nested serializers (Camera, etc.) are broken, this MIGHT fail here too
            pytest.fail(f"AstroImageSerializer Configuration Error: {e}")

    def test_astro_image_detail_serializer_configuration(self) -> None:

        try:
            serializer = AstroImageDetailSerializer()
            # This will trigger field inspection for nested serializers too
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"AstroImageDetailSerializer Configuration Error: {e}")

    def test_main_page_location_serializer_logic(self) -> None:
        """Test custom logic in MainPageLocationSerializer (adventure_date)"""

        # Case 1: Single date (formatted as lower)
        obj = MainPageLocationFactory(
            adventure_date=DateRange(date(2026, 1, 20), date(2026, 1, 21))
        )
        serializer = MainPageLocationSerializer(obj)
        # Expected: 20 Jan 2026
        assert serializer.data["adventure_date"] == "20 Jan 2026"

        # Case 2: Range in same month
        obj2 = MainPageLocationFactory(
            adventure_date=DateRange(date(2026, 1, 20), date(2026, 1, 26))
        )
        serializer2 = MainPageLocationSerializer(obj2)
        assert serializer2.data["adventure_date"] == "20 - 25 Jan 2026"

    def test_tag_serializer_configuration(self) -> None:

        try:
            serializer = TagSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"TagSerializer Configuration Error: {e}")


@pytest.mark.django_db
class TestAstroImageSerializers:
    def test_zoom_serialization_mapping(self) -> None:
        """Test that 'zoom' model field is serialized as 'process' in API"""

        place = PlaceFactory()
        image_zoom_true = AstroImageFactory(zoom=True, place=place)
        image_zoom_false = AstroImageFactory(zoom=False, place=place)

        # The public card serializer should not expose detail-only process state.
        card_data = AstroImageSerializer(image_zoom_true).data
        assert "process" not in card_data

        # Detail payload maps zoom to process for modal/full-resolution behavior.
        data_zoom_true = AstroImageDetailSerializer(image_zoom_true).data
        data_zoom_false = AstroImageDetailSerializer(image_zoom_false).data

        assert "process" in data_zoom_true
        assert data_zoom_true["process"] is True
        assert data_zoom_false["process"] is False
        assert "zoom" not in data_zoom_true

    def test_serializer_consolidation_fields(self) -> None:
        """
        Verify that AstroImageSerializer is card-sized and AstroImageDetailSerializer is detailed.
        """
        place = PlaceFactory()
        image = AstroImageFactory(
            place=place,
            description="Detailed Description",
            exposure_details="ISO 1600",
            processing_details="Stacked in PixInsight",
            astrobin_url="https://astrobin.com/123",
        )

        # Card Serializer - Should NOT have heavy fields (except description)
        card_data = AstroImageSerializer(image).data
        assert "description" in card_data
        assert card_data["description"] == "Detailed Description"
        assert "fallback_image" in card_data
        assert "variants" in card_data
        assert "place" in card_data
        assert "process" not in card_data
        assert "exposure_details" not in card_data
        assert "processing_details" not in card_data
        assert "astrobin_url" not in card_data
        assert "camera" not in card_data  # Should not be present at all for cards

        # Detail Serializer - Should HAVE heavy fields and fallback, but no responsive variants
        detail_data = AstroImageDetailSerializer(image).data
        assert "description" in detail_data
        assert detail_data["description"] == "Detailed Description"
        assert "fallback_image" in detail_data
        assert "variants" not in detail_data
        assert "exposure_details" in detail_data
        assert "processing_details" in detail_data
        assert "astrobin_url" in detail_data
        assert "camera" in detail_data

    def test_image_serializers_omit_dead_fallback_images(self) -> None:
        """Image serializers should omit dead fallback image paths instead of exposing them."""
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(place=PlaceFactory())
        variant = ImageVariantFactory(
            owner=image,
            file__filename="dead-thumbnail.webp",
            role="thumbnail",
            width=560,
            height=373,
        )
        variant.file.storage.delete(str(variant.file.name))

        card_data = AstroImageSerializer(image).data
        detail_data = AstroImageDetailSerializer(image).data

        assert "thumbnail_url" not in card_data
        assert "thumbnail_url" not in detail_data
        assert card_data["fallback_image"] is None
        assert detail_data["fallback_image"] is None

    def test_image_serializers_return_default_thumbnail_fallback_variant(self) -> None:
        """Fallback image should keep the old default thumbnail width behavior."""
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(original=jpeg_field("card-fallback.jpg", size=(1200, 800)))
        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        fallback = image.variants.get(role="thumbnail", width=560)

        card_data = AstroImageSerializer(
            image,
            context={"request": MagicMock(query_params={"size": "840"})},
        ).data
        detail_data = AstroImageDetailSerializer(
            image,
            context={"request": MagicMock(query_params={"size": "840"})},
        ).data

        expected = {
            "url": fallback.file.url,
            "width": 560,
            "height": 373,
            "mime_type": "image/webp",
        }
        assert card_data["fallback_image"] == expected
        assert detail_data["fallback_image"] == expected
        assert [variant["width"] for variant in card_data["variants"]["thumbnail"]] == [
            320,
            560,
        ]

    def test_astro_image_serializer_exposes_thumbnail_variant_candidates(self) -> None:
        """Gallery card payloads should include thumbnail preview candidates."""
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory()
        thumbnail = ImageVariantFactory(
            owner=image,
            file__filename="andromeda-thumbnail-560.webp",
            role="thumbnail",
            width=560,
            height=373,
        )

        data = AstroImageSerializer(image).data

        assert "card" not in data["variants"]
        assert data["variants"]["thumbnail"] == [
            {
                "url": thumbnail.file.url,
                "width": 560,
                "height": 373,
                "mime_type": "image/webp",
            },
        ]


class TestMainPageBackgroundImageSerializer:
    def test_serializer_uses_hero_variant_payload(self) -> None:
        background = MagicMock()
        payload = {
            "fallback_image": {
                "url": "/media/backgrounds/hero.webp",
                "width": 2560,
                "height": 1440,
                "mime_type": "image/webp",
            },
            "variants": {
                "hero": [
                    {
                        "url": "/media/backgrounds/hero.webp",
                        "width": 2560,
                        "height": 1440,
                        "mime_type": "image/webp",
                    }
                ]
            },
        }
        background.get_variant_payload.return_value = payload
        serializer = MainPageBackgroundImageSerializer()

        assert serializer.to_representation(background) == payload
        background.get_variant_payload.assert_called_once_with(
            "hero",
            fallback_width=2560,
        )

    @pytest.mark.django_db
    def test_serializer_exposes_hero_variant_candidates(self) -> None:
        background = MainPageBackgroundImageFactory()
        hero_tablet = ImageVariantFactory(
            owner=background,
            file__filename="background-1280.webp",
            role="hero",
            width=1280,
            height=720,
        )
        hero_desktop = ImageVariantFactory(
            owner=background,
            file__filename="background-1920.webp",
            role="hero",
            width=1920,
            height=1080,
        )

        data = MainPageBackgroundImageSerializer(background).data

        assert data["variants"]["hero"] == [
            {
                "url": hero_tablet.file.url,
                "width": 1280,
                "height": 720,
                "mime_type": "image/webp",
            },
            {
                "url": hero_desktop.file.url,
                "width": 1920,
                "height": 1080,
                "mime_type": "image/webp",
            },
        ]


@pytest.mark.django_db
class TestTranslationSerializers:

    def test_astro_image_serializer_calls_translation_service_with_lang(
        self, mocker: MockerFixture
    ) -> None:
        """Test that AstroImageSerializer calls service when lang is present"""

        mock_translate = mocker.patch("translation.services.TranslationService.get_translation")
        mock_translate.return_value = "Translated Text"
        request = mocker.MagicMock()
        request.query_params.get.return_value = "pl"

        place = PlaceFactory()
        instance = AstroImageFactory(
            name="Original Name",
            slug="test-slug-trans",
            description="Original Description",
            capture_date="2025-01-01",
            place=place,
        )

        serializer = AstroImageSerializer(instance, context={"request": request})
        data = serializer.data

        assert data["description"] == "Translated Text"
        mock_translate.assert_any_call(instance, "description", "pl")

    def test_main_page_location_serializer_calls_translation_service(
        self, mocker: MockerFixture
    ) -> None:

        mock_translate = mocker.patch("translation.services.TranslationService.get_translation")
        mock_translate.return_value = "Translated Text"
        request = mocker.MagicMock()
        request.query_params.get.return_value = "pl"

        place = PlaceFactory()
        instance = MainPageLocationFactory(place=place, highlight_name="Highlights")
        serializer = MainPageLocationSerializer(instance, context={"request": request})
        data = serializer.data

        assert data["highlight_name"] == "Translated Text"
        mock_translate.assert_any_call(instance, "highlight_name", "pl")

    def test_serializer_ignores_translation_without_lang(self, mocker: MockerFixture) -> None:
        """Test that serializers return original data when lang is missing or en"""

        request = mocker.MagicMock()
        request.query_params.get.return_value = None

        place = PlaceFactory()
        instance = AstroImageFactory(
            name="Original", slug="slug-no-lang-trans", capture_date="2025-01-01", place=place
        )

        mock_translate = mocker.patch("translation.services.TranslationService.get_translation")
        serializer = AstroImageSerializer(instance, context={"request": request})
        data = serializer.data

        assert data["name"] == "Original"
        mock_translate.assert_not_called()


@pytest.mark.django_db
class TestTagTranslationSerializers:
    def test_astro_image_serializer_returns_translated_tags(self, mocker: MockerFixture) -> None:
        """Test that AstroImageSerializer returns translated tag names"""
        mock_translate = mocker.patch("translation.services.TranslationService.get_translation")

        # Setup mock behavior
        def side_effect(instance, field, lang):
            if lang == "pl":
                return f"Translated {instance.name}"
            return instance.name

        mock_translate.side_effect = side_effect

        request = mocker.MagicMock()
        request.query_params.get.return_value = "pl"

        place = PlaceFactory()
        image = AstroImageFactory(place=place)
        tag1 = Tag.objects.create(name="Stars")
        tag2 = Tag.objects.create(name="Galaxy")
        image.tags.add(tag1, tag2)

        # Test AstroImageDetailSerializer
        serializer = AstroImageDetailSerializer(image, context={"request": request})
        data = serializer.data

        assert "tags" in data
        assert any(t["name"] == "Translated Stars" for t in data["tags"])
        assert any(t["name"] == "Translated Galaxy" for t in data["tags"])

        # Test AstroImageSerializer
        serializer_list = AstroImageSerializer(image, context={"request": request})
        data_list = serializer_list.data

        assert "tags" in data_list
        assert any(t["name"] == "Translated Stars" for t in data_list["tags"])
        assert any(t["name"] == "Translated Galaxy" for t in data_list["tags"])

    def test_astro_image_serializer_tags_fallback_to_english_on_missing_translation(
        self, mocker: MockerFixture
    ) -> None:
        """Test that tags fall back to English when requested translation is missing."""
        request = mocker.MagicMock()
        request.query_params.get.return_value = "pl"

        place = PlaceFactory()
        image = AstroImageFactory(place=place)
        tag = Tag.objects.create(name="No Translation")
        image.tags.add(tag)

        # Ensure no translation exists for 'pl'
        # By default, Tag.objects.create only creates the default language translation.

        serializer = AstroImageSerializer(image, context={"request": request})
        # The serializer calls TranslationService.get_translation(tag, "name", "pl")
        # which should fall back to the default English translation.
        assert serializer.data["tags"][0]["name"] == "No Translation"
