import pytest
from unittest.mock import patch
from django.urls import reverse
from astrophotography.models import AstroImage, Camera, Lens, MainPageBackgroundImage, Place
from astrophotography.tests.factories import (
    PlaceFactory, AstroImageFactory, CameraFactory, LensFactory, MainPageBackgroundImageFactory
)

@pytest.mark.django_db
class TestAstroImageAdmin:
    def test_admin_list_displays_name(self, admin_client):
        """
        Verify that the AstroImage list view in Admin displays the translated name.
        """
        # Create an image with an English name
        image = AstroImageFactory()
        
        # URL for the change list
        url = reverse("admin:astrophotography_astroimage_changelist")
        
        # Get the page as admin
        response = admin_client.get(url)
        
        # Check success
        assert response.status_code == 200
        
        # Check that the name is in the response content
        content = response.content.decode("utf-8")
        assert image.name in content

    def test_admin_change_page_displays_fields(self, admin_client):
        """
        Verify that the AstroImage change page loads without errors and shows translated fields.
        """
        image = AstroImageFactory()
        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk])
        
        response = admin_client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert image.name in content

    def test_admin_change_page_filtering_pl(self, admin_client):
        """
        Verify that non-translatable fields are hidden when editing 'pl' language.
        """
        image = AstroImageFactory()
        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk])
        
        # Request with language=pl
        response = admin_client.get(url, {"language": "pl"})
        
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        
        # Translatable field SHOULD be present (label "Name" or value)
        assert "Name" in content
        
        # Shared fields SHOULD NOT be present
        assert "Capture Date" not in content
        assert "Place/City" not in content
        assert "Astrobin URL" not in content


@pytest.mark.django_db
class TestCameraLensAdmin:
    def test_camera_list_display(self, admin_client):
        """
        Verify that the camera model name appears in the admin list view.
        """
        CameraFactory(model="Nikon Z6 Mod")
        url = reverse("admin:astrophotography_camera_changelist")
        
        response = admin_client.get(url)
        content = response.content.decode("utf-8")
        
        assert response.status_code == 200
        assert "Nikon Z6 Mod" in content

    def test_lens_list_display(self, admin_client):
        """
        Verify that the lens model name appears in the admin list view.
        """
        LensFactory(model="Nikkor Z 20mm f/1.8")
        url = reverse("admin:astrophotography_lens_changelist")
        
        response = admin_client.get(url)
        content = response.content.decode("utf-8")
        
        assert response.status_code == 200
        assert "Nikkor Z 20mm f/1.8" in content


@pytest.mark.django_db
class TestMainPageBackgroundImageAdmin:
    def test_admin_changelist_view(self, admin_client):
        url = reverse("admin:astrophotography_mainpagebackgroundimage_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "Main Page Background" in response.content.decode("utf-8")

    def test_admin_change_view(self, admin_client):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from io import BytesIO
        from PIL import Image

        img = Image.new('RGB', (1, 1), color='red')
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        image_file = SimpleUploadedFile("test_bg_admin.png", img_io.read(), content_type="image/png")

        bg_image = MainPageBackgroundImageFactory(path=image_file)
        bg_image.set_current_language("en")
        bg_image.name = "Admin Existing BG"
        bg_image.save()

        url = reverse("admin:astrophotography_mainpagebackgroundimage_change", args=[bg_image.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "Admin Existing BG" in response.content.decode("utf-8")


@pytest.mark.django_db
class TestPlaceAdmin:
    @patch('core.services.GPTTranslationAgent')
    def test_save_model_triggers_translation_on_create(self, mock_agent_class, admin_client):
        """Test that creating a new Place via Admin triggers translation service."""
        mock_agent_instance = mock_agent_class.return_value
        mock_agent_instance.translate_place.return_value = "Hawaje"
        
        url = reverse("admin:astrophotography_place_add")
        data = {
            "name": "Hawaii",
            "country": "US",
            "_save": "Save"
        }
        
        response = admin_client.post(url, data)
        assert response.status_code == 302 # Redirect on success
        
        # Verify Place exists
        place = Place.objects.get(translations__name="Hawaii")
        assert place.country == "US"
        
        # Verify agent was called correctly via TranslationService
        mock_agent_instance.translate_place.assert_called_with("Hawaii", "pl", "US")
        
        # Verify translation was saved
        place.set_current_language("pl")
        assert place.name == "Hawaje"

    @patch('core.services.GPTTranslationAgent')
    def test_save_model_triggers_translation_on_name_change(self, mock_agent_class, admin_client):
        """Test that updating Place name via Admin triggers translation service."""
        mock_agent_instance = mock_agent_class.return_value
        mock_agent_instance.translate_place.return_value = "Grecja"
        
        # 1. Create initial place
        place = PlaceFactory(name="Greece", country="GR")
        
        url = reverse("admin:astrophotography_place_change", args=[place.pk])
        data = {
            "name": "New Greece",
            "country": "GR",
            "_save": "Save"
        }
        
        response = admin_client.post(url, data)
        assert response.status_code == 302
        
        # Verify agent called with NEW name
        mock_agent_instance.translate_place.assert_called_with("New Greece", "pl", "GR")

    @patch('core.services.GPTTranslationAgent')
    def test_save_model_does_not_trigger_translation_if_no_name_change(self, mock_agent_class, admin_client):
        """Test that updating fields other than name does not trigger translations."""
        mock_agent_instance = mock_agent_class.return_value
        
        # 1. Create initial place
        place = PlaceFactory(name="Italy", country="IT")
        
        # Initial translation check
        place.set_current_language("pl")
        place.name = "Włochy"
        place.save()

        url = reverse("admin:astrophotography_place_change", args=[place.pk])
        data = {
            "name": "Italy", # Unchanged
            "country": "GR", # Changed country
            "_save": "Save"
        }
        
        response = admin_client.post(url, data)
        assert response.status_code == 302
        
        # Verify agent was NOT called because name didn't change
        mock_agent_instance.translate_place.assert_not_called()


@pytest.mark.django_db
class TestAdminDebug:
    def test_admin_dynamic_mixin_debug(self, admin_client):
        """Verify that the dynamic CSS link is injected and returns expected content."""
        image = AstroImageFactory()
        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk])
        
        response = admin_client.get(url) 
        content = response.content.decode("utf-8")
        
        # 1. Verify the link tag is present in the HTML
        assert '<link href="/admin/dynamic-parler-fixes.css" media="all" rel="stylesheet">' in content

        # 2. Verify the CSS endpoint itself returns the expected generated CSS
        css_url = reverse("admin-dynamic-css")
        css_response = admin_client.get(css_url)
        assert css_response.status_code == 200
        assert "Dynamic Parler CSS generated for default language" in css_response.content.decode("utf-8")

    def test_tabs_structure_multilang(self, admin_client):
        """Create object with EN and PL translations and check tabs structure."""
        image = AstroImageFactory()
        image.set_current_language("pl")
        image.name = "Pl Name"
        image.save()
        
        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk]) + "?language=en"
        response = admin_client.get(url) 
        content = response.content.decode("utf-8")
        
        assert '<div class="parler-language-tabs">' in content

