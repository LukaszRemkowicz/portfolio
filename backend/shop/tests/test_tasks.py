import pytest
from pytest_mock import MockerFixture

from common.tests.image_helpers import _jpeg_field, _png_field
from shop.models import ShopSettings
from shop.tasks import process_shop_settings_images_task


@pytest.mark.django_db
class TestShopSettingsImageProcessing:
    def test_process_task_uses_cropped_image_when_present(self, mocker: MockerFixture) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_jpeg_field("background-source.jpg"),
            image_cropped=_png_field("background-crop.png", size=(1920, 1080)),
            title="Shop",
        )

        convert_mock = mocker.patch(
            "shop.tasks.convert_to_webp", return_value=("ignored", _png_field("background.webp"))
        )
        save_mock = mocker.patch.object(ShopSettings, "save")
        logger_mock = mocker.patch("shop.tasks.logger")

        process_shop_settings_images_task(settings_obj.pk)

        convert_mock.assert_called_once()
        assert convert_mock.call_args.args[0] == settings_obj.image_cropped
        save_mock.assert_called_once()
        assert logger_mock.info.called

    def test_process_task_clears_webp_when_no_source_image(self, mocker: MockerFixture) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_jpeg_field("background-source.jpg"),
            title="Shop",
        )
        settings_obj.image = None
        settings_obj.image_cropped = None

        save_mock = mocker.patch.object(ShopSettings, "save")

        process_shop_settings_images_task(settings_obj.pk)

        save_mock.assert_called_once()
