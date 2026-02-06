from datetime import date

import pytest
from psycopg2.extras import DateRange
from pytest_mock import MockerFixture

from astrophotography.models import MainPageLocation
from astrophotography.serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    CameraSerializer,
    LensSerializer,
    MainPageLocationSerializer,
    MeteorsMainPageConfigSerializer,
    PlaceSerializer,
    TagSerializer,
    TelescopeSerializer,
    TrackerSerializer,
    TripodSerializer,
)
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
)


@pytest.mark.django_db
class TestEquipmentSerializers:
    def test_tracker_serializer_configuration(self) -> None:
        """
        Regression test: Ensure TrackerSerializer has 'fields' or 'exclude' defined.
        Failed in production with AssertionError because Meta overrides parent
        without defining fields.
        """
        try:
            # initializing is enough? Accessing .fields triggers the introspection
            serializer = TrackerSerializer()
            # Access fields to trigger the validation logic inside DRF
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"TrackerSerializer Configuration Error: {e}")

    def test_tripod_serializer_configuration(self) -> None:

        try:
            serializer = TripodSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"TripodSerializer Configuration Error: {e}")

    def test_camera_serializer_configuration(self) -> None:

        try:
            serializer = CameraSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"CameraSerializer Configuration Error: {e}")

    def test_lens_serializer_configuration(self) -> None:

        try:
            serializer = LensSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"LensSerializer Configuration Error: {e}")

    def test_telescope_serializer_configuration(self) -> None:

        try:
            serializer = TelescopeSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"TelescopeSerializer Configuration Error: {e}")

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
        data_list_true = AstroImageSerializerList(image_zoom_true).data
        assert data_list_true["process"] is True


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
