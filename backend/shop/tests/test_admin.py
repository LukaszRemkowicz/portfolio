import pytest
from bs4 import BeautifulSoup

from django.urls import reverse

from common.tests.image_helpers import _jpeg_field
from shop.admin import ShopProductAdmin
from shop.models import ShopSettings
from shop.tests.factories import ShopProductFactory


@pytest.mark.django_db
class TestShopProductAdmin:
    def test_changelist_uses_translated_title_fallback(self, admin_client) -> None:
        product = ShopProductFactory(title="")
        product.set_current_language("pl")
        product.title = "Polski tytul"
        product.save()

        response = admin_client.get(reverse("admin:shop_shopproduct_changelist"))

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")
        title_link = soup.select_one("th.field-get_title a")
        assert title_link is not None
        assert title_link.get_text(strip=True) == "Polski tytul"

    def test_add_view_uses_admin_visible_tab_panel_for_fk_cropper(
        self, admin_client, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            ShopProductAdmin,
            "cropper_visible_tab_panel",
            property(lambda self: "custom-media-tab"),
        )
        url = reverse("admin:shop_shopproduct_add")

        response = admin_client.get(url)

        assert response.status_code == 200
        cropper_data = response.context["admin_fk_image_cropper"]
        assert cropper_data["visible_tab_panel"] == "custom-media-tab"

        soup = BeautifulSoup(response.content, "html.parser")
        cropper_root = soup.select_one("[data-admin-fk-image-cropper-root]")
        assert cropper_root is not None
        assert cropper_root["data-visible-tab-panel"] == "custom-media-tab"

    def test_add_view_injects_fk_cropper_context(self, admin_client) -> None:
        url = reverse("admin:shop_shopproduct_add")
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "admin_fk_image_cropper" in response.context

        cropper_data = response.context["admin_fk_image_cropper"]
        assert cropper_data["visible_tab_panel"] == "media-tab"
        assert cropper_data["source_image_url"] == ""
        assert cropper_data["crop_aspect_ratio"] == pytest.approx(4 / 3)
        assert cropper_data["output_width"] == 560
        assert cropper_data["output_height"] == 420

        soup = BeautifulSoup(response.content, "html.parser")
        cropper_root = soup.select_one("[data-admin-fk-image-cropper-root]")
        assert cropper_root is not None
        assert cropper_root["data-visible-tab-panel"] == cropper_data["visible_tab_panel"]

    def test_change_view_injects_fk_cropper_context(self, admin_client) -> None:
        product = ShopProductFactory()

        url = reverse("admin:shop_shopproduct_change", args=[product.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "admin_fk_image_cropper" in response.context

        cropper_data = response.context["admin_fk_image_cropper"]
        assert cropper_data["field_name"] == "image"
        assert cropper_data["target_field_name"] == "thumbnail_cropped"
        assert cropper_data["visible_tab_panel"] == "media-tab"
        assert cropper_data["crop_aspect_ratio"] == pytest.approx(4 / 3)
        assert cropper_data["output_width"] == 560
        assert cropper_data["output_height"] == 420

        soup = BeautifulSoup(response.content, "html.parser")
        cropper_root = soup.select_one("[data-admin-fk-image-cropper-root]")
        assert cropper_root is not None
        assert cropper_root["data-visible-tab-panel"] == cropper_data["visible_tab_panel"]
        assert soup.select_one("[data-admin-fk-image-cropper-field-select]") is None


@pytest.mark.django_db
class TestShopSettingsAdmin:
    def test_add_view_injects_cropper_context(self, admin_client) -> None:
        url = reverse("admin:shop_shopsettings_add")
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "admin_image_cropper" in response.context

        cropper_data = response.context["admin_image_cropper"]
        assert cropper_data["visible_tab_panel"] == "background-image-tab"
        assert cropper_data["default_field_name"] == "image"

        soup = BeautifulSoup(response.content, "html.parser")
        cropper_root = soup.select_one("[data-admin-image-cropper-root]")
        assert cropper_root is not None
        content = response.content.decode("utf-8")
        assert "/static/astrophotography/js/admin_upload_progress.js" in content
        assert "/static/astrophotography/css/admin_upload_progress.css" in content

    def test_change_view_injects_cropper_context(self, admin_client) -> None:
        settings_obj = ShopSettings.objects.create(
            title="Shop", image=_jpeg_field("settings-bg.jpg")
        )

        url = reverse("admin:shop_shopsettings_change", args=[settings_obj.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "admin_image_cropper" in response.context

        cropper_data = response.context["admin_image_cropper"]
        assert cropper_data["visible_tab_panel"] == "background-image-tab"
        assert cropper_data["default_field_name"] == "image"
        assert cropper_data["fields"][0]["target_field_name"] == "image_cropped"

        soup = BeautifulSoup(response.content, "html.parser")
        cropper_root = soup.select_one("[data-admin-image-cropper-root]")
        assert cropper_root is not None
        content = response.content.decode("utf-8")
        assert 'uploadProgressFieldNames = "image,image_cropped"' in content

    def test_change_view_shows_translation_status_on_default_language(self, admin_client) -> None:
        settings_obj = ShopSettings.objects.create(
            title="Shop", image=_jpeg_field("settings-bg.jpg")
        )

        url = reverse("admin:shop_shopsettings_change", args=[settings_obj.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert b"Translation Status" in response.content
