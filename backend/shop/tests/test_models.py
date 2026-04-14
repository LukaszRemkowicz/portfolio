import pytest
from pytest_mock import MockerFixture

from common.tests.image_helpers import _png_field
from shop.models import ShopProduct
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
def test_save_clears_thumbnail_crop_when_source_image_changes() -> None:
    product = ShopProductFactory()
    product.thumbnail_cropped = _png_field("first-crop.png", size=(560, 560))
    product.save()

    replacement = ShopProductFactory().image
    product.image = replacement
    product.save()
    product.refresh_from_db()

    assert product.image == replacement
    assert not product.thumbnail_cropped


@pytest.mark.django_db
def test_save_keeps_thumbnail_crop_when_only_crop_changes() -> None:
    product = ShopProductFactory()

    product.thumbnail_cropped = _png_field("fresh-crop.png", size=(560, 560))
    product.save()
    product.refresh_from_db()

    assert product.thumbnail_cropped
    assert "fresh-crop" in product.thumbnail_cropped.name


@pytest.mark.django_db
def test_get_thumbnail_prefers_cropped_image() -> None:
    product = ShopProductFactory()
    product.thumbnail_cropped = _png_field("card-crop.png", size=(560, 560))
    product.save()

    assert "card-crop" in product.get_thumbnail()


@pytest.mark.django_db
def test_get_thumbnail_spec_matches_shop_card_output() -> None:
    product = ShopProductFactory()
    spec = product.get_thumbnail_spec()

    assert spec.dimension == 560
    assert spec.aspect_ratio == pytest.approx(4 / 3)


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
