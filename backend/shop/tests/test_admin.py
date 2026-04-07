# backend/shop/tests/test_admin.py
import pytest
from bs4 import BeautifulSoup

from django.urls import reverse

from shop.tests.factories import ShopProductFactory


@pytest.mark.django_db
class TestShopProductAdmin:
    """Tests for the ShopProduct admin interface, especially the cropper context."""

    def test_change_view_injects_cropper_context(self, admin_client):
        """
        GIVEN an existing ShopProduct
        WHEN the admin change_view is accessed
        THEN the image cropper UI components are present in the response
        """
        product = ShopProductFactory()

        url = reverse("admin:shop_shopproduct_change", args=[product.pk])
        response = admin_client.get(url)

        assert response.status_code == 200

        # Check in context
        assert "admin_image_cropper" in response.context
        cropper_data = response.context["admin_image_cropper"]

        assert cropper_data["component_title"] == "Image Cropper"
        assert len(cropper_data["fields"]) == 1

        field_config = cropper_data["fields"][0]
        assert field_config["field_name"] == "path"
        assert field_config["target_field_name"] == "path_cropped"

        # Verify the custom template is actually used
        soup = BeautifulSoup(response.content, "html.parser")
        # Look for the React root div defined in our robust_change_form.html
        cropper_root = soup.find(id="image-cropper-root")
        assert cropper_root is not None, "Cropper React mount point missing"
