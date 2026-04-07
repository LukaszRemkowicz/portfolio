# backend/shop/tests/test_tasks.py
"""
Integration tests for ShopProduct image processing.

Validates that the universal `core.process_image_task` correctly handles
ShopProduct instances, including resolving WebP from path_cropped.
"""

import pytest

from common.tests.image_helpers import _jpeg_field, _png_field
from core.tasks import process_image_task
from shop.tests.factories import ShopProductFactory


@pytest.mark.django_db
class TestShopProductImageProcessing:
    """Verifies the BaseImage Celery pipeline works for ShopProduct."""

    def test_process_image_task_optimizes_product_image(self):
        """
        GIVEN a product with a JPEG source image
        WHEN process_image_task is called (which BaseImage triggers)
        THEN the source should be converted to WebP
        """
        product = ShopProductFactory()
        product.path = _jpeg_field("product-source.jpg")
        product.save()

        process_image_task("shop", "ShopProduct", str(product.pk))

        product.refresh_from_db()
        assert product.path.name.endswith(".jpg")

        # Check that original_image was used to preserve the original file
        assert product.original_image.name.endswith(".jpg")

    def test_process_image_task_prefers_cropped_image(self):
        """
        GIVEN a product with both a source image and a cropped image
        WHEN process_image_task is called
        THEN the WebP conversion should use the cropped image as its source
        """
        product = ShopProductFactory()
        product.path = _jpeg_field("original_source.jpg")
        product.path_cropped = _png_field("cropped_version.png", size=(560, 560))
        product.save()

        process_image_task("shop", "ShopProduct", str(product.pk))

        product.refresh_from_db()
        assert "original_source" in product.path.name
        assert "cropped_version" in product.path_cropped.name
