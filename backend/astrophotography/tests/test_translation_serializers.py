from unittest.mock import MagicMock, patch

import pytest

from astrophotography.models import AstroImage, MainPageLocation
from astrophotography.serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    MainPageLocationSerializer,
)
from users.models import User
from users.serializers import UserSerializer


@pytest.mark.django_db
class TestTranslationSerializers:

    @patch("core.services.TranslationService.get_translated_field")
    def test_astro_image_serializer_calls_translation_service_with_lang(self, mock_translate):
        """Test that AstroImageSerializer calls service when lang is present"""
        mock_translate.return_value = "Translated Text"

        # Mock request with ?lang=pl
        request = MagicMock()
        request.query_params.get.return_value = "pl"

        instance = AstroImage.objects.create(
            name="Original Name",
            slug="test-slug",
            description="Original Description",
            capture_date="2025-01-01",
        )

        serializer = AstroImageSerializer(instance, context={"request": request})
        data = serializer.data

        # Should call translation for Description
        assert data["description"] == "Translated Text"
        # Since 'name' is in the serializer fields list for AstroImageSerializer?
        # Actually usually name is in List serializer, description in Detail.
        # Let's check serializer definition later, but assuming generic behavior.

        mock_translate.assert_any_call(instance, "description", "pl")

    @patch("core.services.TranslationService.get_translated_field")
    def test_astro_image_list_serializer_calls_translation_service(self, mock_translate):
        mock_translate.return_value = "Translated Text"
        request = MagicMock()
        request.query_params.get.return_value = "pl"

        instance = AstroImage.objects.create(
            name="Original", slug="slug-2", description="Desc", capture_date="2025-01-01"
        )
        serializer = AstroImageSerializerList(instance, context={"request": request})
        data = serializer.data

        assert data["name"] == "Translated Text"
        mock_translate.assert_any_call(instance, "name", "pl")

    @patch("core.services.TranslationService.get_translated_field")
    def test_main_page_location_serializer_calls_translation_service(self, mock_translate):
        mock_translate.return_value = "Translated Text"
        request = MagicMock()
        request.query_params.get.return_value = "pl"

        instance = MainPageLocation.objects.create(highlight_name="Highlights")
        serializer = MainPageLocationSerializer(instance, context={"request": request})
        data = serializer.data

        assert data["highlight_name"] == "Translated Text"
        mock_translate.assert_any_call(instance, "highlight_name", "pl")

    @patch("core.services.TranslationService.get_translated_field")
    def test_user_serializer_calls_translation_service(self, mock_translate):
        mock_translate.return_value = "Translated Text"
        request = MagicMock()
        request.query_params.get.return_value = "pl"

        # Singleton user
        instance = User.objects.create(email="test@example.com", short_description="Original")
        serializer = UserSerializer(instance, context={"request": request})
        data = serializer.data

        assert data["short_description"] == "Translated Text"
        mock_translate.assert_any_call(instance, "short_description", "pl")

    def test_serializer_ignores_translation_without_lang(self):
        """Test that serializers return original data when lang is missing or en"""
        request = MagicMock()
        request.query_params.get.return_value = None  # or "en"

        instance = AstroImage.objects.create(
            name="Original", slug="slug-no-lang", capture_date="2025-01-01"
        )

        # Use patch context to ensure it's NOT called
        with patch("core.services.TranslationService.get_translated_field") as mock_translate:
            serializer = AstroImageSerializerList(instance, context={"request": request})
            data = serializer.data

            assert data["name"] == "Original"
            mock_translate.assert_not_called()
