import pytest

from astrophotography.serializers import TrackerSerializer


@pytest.mark.django_db
class TestEquipmentSerializers:
    def test_tracker_serializer_configuration(self):
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

    def test_tripod_serializer_configuration(self):
        """
        Regression test: Ensure TripodSerializer also has 'fields' or 'exclude' defined.
        """
        from astrophotography.serializers import TripodSerializer

        try:
            serializer = TripodSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"TripodSerializer Configuration Error: {e}")

    def test_camera_serializer_configuration(self):
        from astrophotography.serializers import CameraSerializer

        try:
            serializer = CameraSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"CameraSerializer Configuration Error: {e}")

    def test_lens_serializer_configuration(self):
        from astrophotography.serializers import LensSerializer

        try:
            serializer = LensSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"LensSerializer Configuration Error: {e}")

    def test_telescope_serializer_configuration(self):
        from astrophotography.serializers import TelescopeSerializer

        try:
            serializer = TelescopeSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"TelescopeSerializer Configuration Error: {e}")

    def test_place_serializer_configuration(self):
        from astrophotography.serializers import PlaceSerializer

        try:
            serializer = PlaceSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"PlaceSerializer Configuration Error: {e}")

    def test_meteors_config_serializer_configuration(self):
        from astrophotography.serializers import MeteorsMainPageConfigSerializer

        try:
            # Should have explicit fields
            serializer = MeteorsMainPageConfigSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"MeteorsMainPageConfigSerializer Configuration Error: {e}")

    def test_astro_image_serializer_configuration(self):
        from astrophotography.serializers import AstroImageSerializer

        try:
            serializer = AstroImageSerializer()
            # This will trigger field inspection for nested serializers too
            _ = serializer.fields
        except AssertionError as e:
            # If nested serializers (Camera, etc.) are broken, this MIGHT fail here too
            pytest.fail(f"AstroImageSerializer Configuration Error: {e}")

    def test_main_page_location_serializer_logic(self):
        """Test custom logic in MainPageLocationSerializer (adventure_date)"""
        from datetime import date

        from psycopg2.extras import DateRange

        from astrophotography.serializers import MainPageLocationSerializer
        from astrophotography.tests.factories import MainPageLocationFactory

        # Case 1: Single date (formatted as lower)
        obj = MainPageLocationFactory(
            adventure_date=DateRange(date(2026, 1, 20), date(2026, 1, 21))
        )
        serializer = MainPageLocationSerializer(obj)
        # Expected: 20 Jan 2026
        # Logic: upper is Jan 21. display_upper = Jan 20. lower == display_upper.
        assert serializer.data["adventure_date"] == "20 Jan 2026"

        # Case 2: Range in same month
        obj2 = MainPageLocationFactory(
            adventure_date=DateRange(date(2026, 1, 20), date(2026, 1, 26))
        )  # upper is exclusive? Logic says yes.
        # display_upper = Jan 25.
        serializer2 = MainPageLocationSerializer(obj2)
        assert serializer2.data["adventure_date"] == "20 - 25 Jan 2026"

    def test_tag_serializer_configuration(self):
        from astrophotography.serializers import TagSerializer

        try:
            serializer = TagSerializer()
            _ = serializer.fields
        except AssertionError as e:
            pytest.fail(f"TagSerializer Configuration Error: {e}")
