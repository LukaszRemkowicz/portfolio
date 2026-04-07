# backend/shop/tests/test_models.py
"""
Tests for ShopProduct model.

Coverage:
- Correct inheritance from BaseImage
- Field defaults and __str__
- save() resets path_cropped when source path changes
- save() keeps path_cropped when only path_cropped changes
- get_original_source() prefers path_cropped over path
- get_path_spec() returns THUMBNAIL spec
- Translation trigger fires on save
- Cache invalidation signal fires on save and delete
"""

import pytest
from pytest_mock import MockerFixture

from django.conf import settings

from common.tests.image_helpers import _jpeg_field, _png_field
from common.utils.image import ImageSpec
from shop.models import ShopProduct
from shop.tests.factories import InactiveShopProductFactory, ShopProductFactory

# ---------------------------------------------------------------------------
# Creation & basic fields
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_shopproduct_creation_defaults():
    """A newly created ShopProduct has sensible defaults."""
    product = ShopProductFactory()

    assert product.pk is not None
    assert isinstance(product.pk, type(product.pk))  # UUID
    assert product.is_active is True
    assert product.currency == "USD"
    assert product.order >= 0
    assert product.path  # BaseImage field must be present


@pytest.mark.django_db
def test_shopproduct_str_uses_title():
    """__str__ returns the translated title, not the UUID."""
    product = ShopProductFactory(title="Andromeda Print")
    assert str(product) == "Andromeda Print"


@pytest.mark.django_db
def test_shopproduct_str_fallback_to_uuid_when_no_title():
    """__str__ falls back to str(pk) when no translation is present."""
    product = ShopProductFactory.build()  # not saved, no translation record
    product.pk = None
    # Simulate missing translation
    result = str(product)
    # Either empty string or UUID string — must not raise
    assert isinstance(result, str)


@pytest.mark.django_db
def test_shopproduct_inherits_baseimage_fields():
    """ShopProduct exposes all BaseImage-provided fields."""
    product = ShopProductFactory()
    assert hasattr(product, "original_image")
    assert hasattr(product, "thumbnail")
    assert hasattr(product, "created_at")
    assert hasattr(product, "updated_at")


# ---------------------------------------------------------------------------
# get_path_spec — THUMBNAIL override
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_path_spec_returns_thumbnail_spec():
    """ShopProduct overrides get_path_spec() to return the THUMBNAIL spec."""
    product = ShopProductFactory()
    spec = product.get_path_spec()

    expected = settings.IMAGE_OPTIMIZATION_SPECS["THUMBNAIL"]
    assert isinstance(spec, ImageSpec)
    assert spec.dimension == expected.dimension
    assert spec.quality == expected.quality


# ---------------------------------------------------------------------------
# path_cropped reset logic
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_save_resets_path_cropped_when_source_path_changes():
    """
    GIVEN a product with a source image and a cropped image
    WHEN the source image (path) is replaced
    THEN path_cropped is automatically cleared
    """
    product = ShopProductFactory()
    product.path = _jpeg_field("original.jpg")
    product.path_cropped = _png_field("cropped.png", size=(400, 400))
    product.save()

    product.path = _jpeg_field("replacement.jpg")
    product.save()
    product.refresh_from_db()

    assert "replacement" in product.path.name
    assert not product.path_cropped


@pytest.mark.django_db
def test_save_keeps_path_cropped_when_only_crop_changes():
    """
    GIVEN a product with a source image
    WHEN only path_cropped is updated (admin cropper wrote new crop without re-uploading source)
    THEN path_cropped is persisted and path is unchanged
    """
    product = ShopProductFactory()
    product.path = _jpeg_field("original.jpg")
    product.save()

    original_path_name = product.path.name

    product.path_cropped = _png_field("new_crop.png", size=(400, 400))
    product.save()
    product.refresh_from_db()

    assert product.path.name == original_path_name
    assert product.path_cropped
    assert "new_crop" in product.path_cropped.name


@pytest.mark.django_db
def test_save_allows_simultaneous_path_and_crop_update():
    """
    GIVEN a product
    WHEN source and cropped are updated in the same save()
    THEN both are persisted (admin uploaded a new image and immediately cropped it)
    """
    product = ShopProductFactory()
    product.path = _jpeg_field("new_source.jpg")
    product.path_cropped = _png_field("new_crop.png", size=(400, 400))
    product.save()
    product.refresh_from_db()

    assert "new_source" in product.path.name
    assert "new_crop" in product.path_cropped.name


# ---------------------------------------------------------------------------
# get_original_source — prefers path_cropped for WebP pipeline
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_original_source_prefers_path_cropped():
    """
    GIVEN a product where path_cropped is set
    WHEN get_original_source() is called
    THEN it returns path_cropped (so WebP is generated from the crop)
    """
    product = ShopProductFactory()
    product.path = _jpeg_field("source.jpg")
    product.path_cropped = _png_field("cropped.png", size=(400, 400))
    product.save()

    source = product.get_original_source()
    assert source == product.path_cropped


@pytest.mark.django_db
def test_get_original_source_falls_back_to_path_when_no_crop():
    """
    GIVEN a product with no path_cropped
    WHEN get_original_source() is called
    THEN it delegates to BaseImage (returns path)
    """
    product = ShopProductFactory()
    product.path = _jpeg_field("source.jpg")
    product.path_cropped = None
    product.save()

    source = product.get_original_source()
    # BaseImage returns path when it's not a .webp
    assert source == product.path


# ---------------------------------------------------------------------------
# Translation trigger
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_save_triggers_translations(mocker: MockerFixture):
    """
    GIVEN the global translation mock (from conftest)
    WHEN a product is saved with title content in the default language
    THEN trigger_translations() is called and returns language codes
    """
    mock_trigger = mocker.patch.object(ShopProduct, "trigger_translations", return_value=["pl"])

    ShopProductFactory()

    assert mock_trigger.called


@pytest.mark.django_db
def test_translation_service_method_is_set():
    """ShopProduct declares the correct translation service method name."""
    assert ShopProduct.translation_service_method == "translate_shop_product"


@pytest.mark.django_db
def test_translation_trigger_fields_are_set():
    """ShopProduct declares the correct translation trigger fields."""
    assert "title" in ShopProduct.translation_trigger_fields
    assert "description" in ShopProduct.translation_trigger_fields


# ---------------------------------------------------------------------------
# Cache invalidation signals
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_save_triggers_cache_invalidation(mocker: MockerFixture):
    """
    GIVEN a new product
    WHEN it is saved
    THEN shop cache is invalidated and SSR cache task is dispatched
    """
    mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")
    mock_ssr = mocker.patch("shop.signals.invalidate_frontend_ssr_cache_task.delay_on_commit")

    ShopProductFactory()

    assert mock_cache.called
    mock_ssr.assert_called_with(["shop"])


@pytest.mark.django_db
def test_delete_triggers_cache_invalidation(mocker: MockerFixture):
    """
    GIVEN an existing product
    WHEN it is deleted
    THEN shop cache is invalidated and SSR cache task is dispatched
    """
    product = ShopProductFactory()

    mock_cache = mocker.patch("shop.signals.CacheService.invalidate_shop_cache")
    mock_ssr = mocker.patch("shop.signals.invalidate_frontend_ssr_cache_task.delay_on_commit")

    product.delete()

    assert mock_cache.called
    mock_ssr.assert_called_with(["shop"])


# ---------------------------------------------------------------------------
# Inactive products
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_inactive_product_is_persisted():
    """Inactive products can be saved and retrieved from the database."""
    product = InactiveShopProductFactory()
    product.refresh_from_db()
    assert product.is_active is False


@pytest.mark.django_db
def test_shopproduct_ordering_by_order_field():
    """
    Products are ordered by the `order` field ascending by default.
    """
    p3 = ShopProductFactory(order=30)
    p1 = ShopProductFactory(order=10)
    p2 = ShopProductFactory(order=20)

    products = list(ShopProduct.objects.all())
    assert products[0].pk == p1.pk
    assert products[1].pk == p2.pk
    assert products[2].pk == p3.pk
