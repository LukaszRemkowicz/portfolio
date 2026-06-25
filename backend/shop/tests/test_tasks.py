from unittest.mock import patch

import pytest

from astrophotography.tests.factories import AstroImageFactory
from common.tests.image_helpers import jpeg_field, png_field
from core.tasks import process_image_task
from shop.models import ShopSettings
from shop.tests.factories import ShopProductFactory


@pytest.mark.django_db
class TestShopProductImageProcessing:
    def test_process_task_uses_cropped_image_for_product_variants(self) -> None:
        with patch("shop.models.process_image_task.delay_on_commit"):
            linked_image = AstroImageFactory(
                original__width=1200,
                original__height=800,
            )
            product = ShopProductFactory(
                image=linked_image, image_cropped=jpeg_field("product-crop.jpg", size=(560, 420))
            )

        process_image_task("shop", "ShopProduct", product.pk, ["image_cropped"])

        product.refresh_from_db()
        original_format = product.variants.get(role="original_format")
        thumbnail = product.variants.get(role="thumbnail")
        assert original_format.width == 560
        assert thumbnail.width == 560
        assert thumbnail.file.name.endswith(".webp")
        assert "product-crop" in thumbnail.file.name

    def test_process_task_rebuilds_product_variants_from_linked_image_when_crop_is_removed(
        self,
    ) -> None:
        with patch("shop.models.process_image_task.delay_on_commit"):
            product = ShopProductFactory(
                image_cropped=jpeg_field("product-crop.jpg", size=(560, 420))
            )
        process_image_task("shop", "ShopProduct", product.pk, ["image_cropped"])
        assert product.variants.count() == 2

        product.image_cropped = None
        with patch("shop.models.process_image_task.delay_on_commit"):
            product.save(update_fields=["image_cropped"])

        process_image_task("shop", "ShopProduct", product.pk, ["image_cropped"])

        product.refresh_from_db()
        assert product.variants.count() == 2
        assert product.variants.get(role="original_format").width > 0
        thumbnail = product.variants.get(role="thumbnail")
        assert thumbnail.width > 0
        assert "product-crop" not in thumbnail.file.name


@pytest.mark.django_db
class TestShopSettingsImageProcessing:
    def test_process_task_uses_cropped_image_when_present(self) -> None:
        with patch("shop.models.process_image_task.delay_on_commit"):
            settings_obj = ShopSettings.objects.create(
                image=jpeg_field("background-source.jpg"),
                image_cropped=png_field("background-crop.png", size=(1920, 1080)),
                title="Shop",
            )

        process_image_task("shop", "ShopSettings", settings_obj.pk, ["image"])

        settings_obj.refresh_from_db()
        original_format = settings_obj.variants.get(role="original_format")
        background = settings_obj.variants.get(role="background")
        assert original_format.width == 1920
        assert background.width == 1920
        assert background.file.name.endswith(".webp")
        assert "background-crop" in background.file.name

    def test_process_task_clears_variants_when_no_source_image(self) -> None:
        with patch("shop.models.process_image_task.delay_on_commit"):
            settings_obj = ShopSettings.objects.create(
                image=jpeg_field("background-source.jpg"),
                title="Shop",
            )
        process_image_task("shop", "ShopSettings", settings_obj.pk, ["image"])
        assert settings_obj.variants.count() == 2

        settings_obj.image = None
        settings_obj.image_cropped = None
        with patch("shop.models.process_image_task.delay_on_commit"):
            settings_obj.save(update_fields=["image", "image_cropped"])

        process_image_task("shop", "ShopSettings", settings_obj.pk, ["image"])

        settings_obj.refresh_from_db()
        assert settings_obj.variants.count() == 0
