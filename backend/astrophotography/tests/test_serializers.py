from datetime import date

import pytest
from psycopg2.extras import DateRange
from pytest_mock import MockerFixture

from astrophotography.models import MainPageLocation, Tag
from astrophotography.serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    MainPageLocationSerializer,
    MeteorsMainPageConfigSerializer,
    PlaceSerializer,
    TagSerializer,
)
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
)


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

    def test_main_page_location_serializer_logic(self) -> None:
        """Test custom logic in MainPageLocationSerializer (adventure_date)"""

        # Case 1: Single date (formatted as lower)
        place = PlaceFactory(country="PL", name="Tatras")
        obj = MainPageLocationFactory(
            place=place, adventure_date=DateRange(date(2026, 1, 20), date(2026, 1, 21))
        )
        serializer = MainPageLocationSerializer(obj)
        # Expected: 20 Jan 2026
        assert serializer.data["adventure_date"] == "20 Jan 2026"

        # Case 2: Range in same month
        obj2 = MainPageLocationFactory(
            place=place, adventure_date=DateRange(date(2026, 1, 20), date(2026, 1, 26))
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

        # Test AstroImageSerializer
        data_zoom_true = AstroImageSerializer(image_zoom_true).data
        data_zoom_false = AstroImageSerializer(image_zoom_false).data

        assert "process" in data_zoom_true
        assert data_zoom_true["process"] is True
        assert data_zoom_false["process"] is False
        assert "zoom" not in data_zoom_true

        # Test AstroImageSerializerList

    def test_serializer_consolidation_fields(self) -> None:
        """
        Verify that AstroImageSerializerList is lightweight and AstroImageSerializer is detailed.
        """
        place = PlaceFactory()
        image = AstroImageFactory(
            place=place,
            description="Detailed Description",
            exposure_details="ISO 1600",
            processing_details="Stacked in PixInsight",
            astrobin_url="https://astrobin.com/123",
        )

        # List Serializer - Should NOT have heavy fields (except description)
        list_data = AstroImageSerializerList(image).data
        assert "description" in list_data
        assert list_data["description"] == "Detailed Description"
        assert "exposure_details" not in list_data
        assert "processing_details" not in list_data
        assert "astrobin_url" not in list_data
        assert "camera" not in list_data  # Should not be present at all for list

        # Detail Serializer - Should HAVE heavy fields
        detail_data = AstroImageSerializer(image).data
        assert "description" in detail_data
        assert detail_data["description"] == "Detailed Description"
        assert "exposure_details" in detail_data
        assert "processing_details" in detail_data
        assert "astrobin_url" in detail_data
        assert "camera" in detail_data


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

        instance = MainPageLocation.objects.create(highlight_name="Highlights")
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
        serializer = AstroImageSerializerList(instance, context={"request": request})
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

        # Test AstroImageSerializer (Detail)
        serializer = AstroImageSerializer(image, context={"request": request})
        data = serializer.data

        assert "tags" in data
        assert "Translated Stars" in data["tags"]
        assert "Translated Galaxy" in data["tags"]

        # Test AstroImageSerializerList
        serializer_list = AstroImageSerializerList(image, context={"request": request})
        data_list = serializer_list.data

        assert "tags" in data_list
        assert "Translated Stars" in data_list["tags"]
        assert "Translated Galaxy" in data_list["tags"]

    def test_astro_image_serializer_tags_fallback_to_empty_on_missing_translation(
        self, mocker: MockerFixture
    ) -> None:
        """Test that tags return empty string if translation is missing in non-default lang"""
        # TranslationService already updated to return "" if fallback is False and lang matches
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
        # which should return "" because no 'pl' translation exists.
        assert serializer.data["tags"] == [""]
