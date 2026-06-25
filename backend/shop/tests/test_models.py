import logging
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from astrophotography.tests.factories import AstroImageFactory
from common.tests.image_helpers import jpeg_field, png_field
from common.types import ImageVariantSpec, ViewportWidths
from core.tests.factories import ImageVariantFactory
from shop.models import ShopProduct, ShopSettings
from shop.tests.factories import ShopProductFactory


@pytest.mark.django_db
def test_shopproduct_creation_defaults() -> None:
    product = ShopProductFactory()

    assert product.pk is not None
    assert product.is_active is True
    assert product.currency == "USD"
    assert product.image_id is not None


@pytest.mark.django_db
def test_shopproduct_str_uses_title() -> None:
    product = ShopProductFactory(title="Andromeda Print")
    assert str(product) == "Andromeda Print"


@pytest.mark.django_db
def test_save_clears_image_crop_when_source_image_changes() -> None:
    product = ShopProductFactory()
    product.image_cropped = png_field("first-crop.png", size=(560, 560))
    product.save()

    replacement = ShopProductFactory().image
    product.image = replacement
    product.save()
    product.refresh_from_db()

    assert product.image == replacement
    assert not product.image_cropped


@pytest.mark.django_db
def test_partial_save_clears_product_crop_and_processes_variants(mocker: MockerFixture) -> None:
    product = ShopProductFactory()
    product.image_cropped = png_field("first-crop.png", size=(560, 560))
    product.save()
    replacement = ShopProductFactory().image
    mock_delay = mocker.patch("shop.models.process_image_task.delay_on_commit")

    product.image = replacement
    product.save(update_fields=["image"])
    product.refresh_from_db()

    assert product.image == replacement
    assert not product.image_cropped
    mock_delay.assert_called_once_with(
        "shop",
        "shopproduct",
        product.pk,
        ["image", "image_cropped"],
    )


@pytest.mark.django_db
def test_save_keeps_image_crop_when_only_crop_changes() -> None:
    product = ShopProductFactory()

    product.image_cropped = png_field("fresh-crop.png", size=(560, 560))
    product.save()
    product.refresh_from_db()

    assert product.image_cropped
    assert "fresh-crop" in product.image_cropped.name


@pytest.mark.django_db
def test_image_url_prefers_product_image_variant() -> None:
    product = ShopProductFactory()
    product.image_cropped = png_field("card-crop.png", size=(560, 560))
    product.save()
    variant = product.variants.get(role="thumbnail", width=560)

    assert product.get_image_url("thumbnail", 560) == variant.file.url


@pytest.mark.django_db
def test_image_url_uses_requested_role_and_width(mocker: MockerFixture) -> None:
    mocker.patch.object(
        ShopProduct,
        "image_variant_specs",
        (
            ImageVariantSpec(
                role="card",
                viewport_widths=ViewportWidths.fixed(320),
                quality=90,
            ),
            ImageVariantSpec(
                role="thumbnail",
                viewport_widths=ViewportWidths.fixed(560),
                quality=90,
            ),
        ),
    )
    product = ShopProductFactory()
    variant = ImageVariantFactory(
        image=product,
        file__filename="product-thumbnail.webp",
        role="thumbnail",
        width=560,
        height=420,
    )

    assert product.get_image_url("thumbnail", 560) == variant.file.url


@pytest.mark.django_db
def test_image_url_falls_back_to_cropped_source_when_variant_missing(caplog) -> None:
    product = ShopProductFactory()
    product.image_cropped = png_field("card-crop.png", size=(560, 420))
    product.save()
    product.variants.all().delete()

    with caplog.at_level(logging.INFO):
        assert "card-crop" in product.get_image_url("thumbnail", 560)
    assert "Falling back to product cropped source image" in caplog.text


@pytest.mark.django_db
def test_image_url_falls_back_to_astroimage_thumbnail_when_crop_missing() -> None:
    with patch("core.models.process_image_task.delay_on_commit"):
        astro_image = AstroImageFactory(
            original=jpeg_field("astro-original.jpg", size=(1600, 1200))
        )
    thumbnail_variant = ImageVariantFactory(
        image=astro_image,
        file__filename="astro-thumbnail.webp",
        role="thumbnail",
        width=560,
        height=420,
    )
    product = ShopProductFactory(image=astro_image, image_cropped=None)
    product.variants.all().delete()

    assert product.get_image_url("thumbnail", 560) == thumbnail_variant.file.url


@pytest.mark.django_db
def test_image_url_falls_back_to_astroimage_original_when_thumbnail_variant_missing(
    caplog,
) -> None:
    astro_image = AstroImageFactory(original=jpeg_field("astro-original.jpg", size=(1600, 1200)))
    product = ShopProductFactory(image=astro_image, image_cropped=None)
    product.variants.all().delete()
    astro_image.variants.all().delete()

    assert product.get_image_url("thumbnail", 560) == str(astro_image.original.url)
    assert "Falling back to original source image because variant is missing" in caplog.text


@pytest.mark.django_db
def test_image_variant_sources_use_product_image_crop() -> None:
    product = ShopProductFactory()
    product.image_cropped = png_field("product-crop.png", size=(560, 420))
    product.save()

    source = product.get_image_variant_sources()[0]

    assert source.field_name == "image_cropped"
    assert source.source_image == product.image_cropped
    assert source.upload_dir == "shop/products/cropped"
    assert [spec.role for spec in product.get_image_variant_specs()] == [
        "original_format",
        "thumbnail",
    ]


@pytest.mark.django_db
def test_image_variant_sources_fall_back_to_astroimage_original_when_crop_missing() -> None:
    astro_image = AstroImageFactory(
        original=jpeg_field("astro-product-source.jpg", size=(1600, 1200))
    )
    product = ShopProductFactory(image=astro_image, image_cropped=None)

    source = product.get_image_variant_sources()[0]

    assert source.field_name == "image"
    assert source.source_image == astro_image.original


@pytest.mark.django_db
def test_shopsettings_background_image_url_returns_background_variant() -> None:
    with patch("shop.models.process_image_task.delay_on_commit"):
        settings_obj = ShopSettings.objects.create(
            image=png_field("shop-background.png", size=(1920, 1080))
        )
    background = ImageVariantFactory(
        image=settings_obj,
        file__filename="shop-background-variant.webp",
        role="background",
        width=1920,
        height=1080,
    )

    assert settings_obj.get_background_image_url() == background.file.url


@pytest.mark.django_db
def test_shopsettings_background_image_url_falls_back_when_variant_missing(caplog) -> None:
    with patch("shop.models.process_image_task.delay_on_commit"):
        settings_obj = ShopSettings.objects.create(
            image=png_field("shop-background.png", size=(1920, 1080))
        )

    assert settings_obj.get_background_image_url() == settings_obj.image.url
    assert "Falling back to background source image" in caplog.text


@pytest.mark.django_db
def test_shopsettings_image_url_uses_requested_role_and_width() -> None:
    with patch("shop.models.process_image_task.delay_on_commit"):
        settings_obj = ShopSettings.objects.create(
            image=png_field("shop-background.png", size=(1920, 1080))
        )
    requested = ImageVariantFactory(
        image=settings_obj,
        file__filename="shop-background-960.webp",
        role="background",
        width=960,
        height=540,
    )
    ImageVariantFactory(
        image=settings_obj,
        file__filename="shop-background-1920.webp",
        role="background",
        width=1920,
        height=1080,
    )

    assert settings_obj.get_image_url("background", 960) == requested.file.url


@pytest.mark.django_db
def test_shopsettings_image_url_falls_back_to_background_source_when_variant_missing(
    caplog,
) -> None:
    with patch("shop.models.process_image_task.delay_on_commit"):
        settings_obj = ShopSettings.objects.create(
            image=png_field("shop-background.png", size=(1920, 1080))
        )
    settings_obj.variants.all().delete()

    assert settings_obj.get_image_url("background", 1920) == settings_obj.image.url
    assert "Falling back to background source image" in caplog.text


@pytest.mark.django_db
def test_shopsettings_image_url_logs_error_when_variant_and_source_are_missing(caplog) -> None:
    settings_obj = ShopSettings(image=None)

    assert settings_obj.get_image_url("background", 1920) is None
    assert "Image variant is missing and background source image is unavailable" in caplog.text


@pytest.mark.django_db
def test_partial_save_clears_shopsettings_crop_and_processes_variants(
    mocker: MockerFixture,
) -> None:
    with patch("shop.models.process_image_task.delay_on_commit"):
        settings_obj = ShopSettings.objects.create(
            image=jpeg_field("shop-background.jpg", size=(1920, 1080)),
            image_cropped=png_field("shop-background-crop.png", size=(1920, 1080)),
            title="Prints",
        )
    mock_delay = mocker.patch("shop.models.process_image_task.delay_on_commit")

    settings_obj.image = jpeg_field("shop-background-replacement.jpg", size=(1920, 1080))
    settings_obj.save(update_fields=["image"])
    settings_obj.refresh_from_db()

    assert not settings_obj.image_cropped
    mock_delay.assert_called_once_with(
        "shop",
        "shopsettings",
        settings_obj.pk,
        ["image", "image_cropped"],
    )


@pytest.mark.django_db
def test_save_triggers_translations(mocker: MockerFixture) -> None:
    mock_trigger = mocker.patch.object(ShopProduct, "trigger_translations", return_value=["pl"])

    ShopProductFactory()

    assert mock_trigger.called


@pytest.mark.django_db
def test_save_triggers_cache_invalidation(mocker: MockerFixture) -> None:
    mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")
    mock_ssr = mocker.patch("shop.signals.invalidate_frontend_ssr_cache_task.delay_on_commit")

    ShopProductFactory()

    assert mock_cache.called
    mock_ssr.assert_called_with(["shop"])
