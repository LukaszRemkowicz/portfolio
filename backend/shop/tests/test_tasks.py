import pytest
from pytest_mock import MockerFixture

from common.tests.image_helpers import _jpeg_field, _png_field
from core.tasks import process_image_task
from shop.models import ShopSettings


@pytest.mark.django_db
class TestShopSettingsImageProcessing:
    def test_process_task_uses_cropped_image_when_present(self, mocker: MockerFixture) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_jpeg_field("background-source.jpg"),
            image_cropped=_png_field("background-crop.png", size=(1920, 1080)),
            title="Shop",
        )

        convert_mock = mocker.patch(
            "common.image_processing.convert_to_webp",
            return_value=("ignored", _png_field("background.webp")),
        )
        save_mock = mocker.patch.object(ShopSettings, "save")

        process_image_task("shop", "ShopSettings", settings_obj.pk, ["image"])

        convert_mock.assert_called_once()
        assert convert_mock.call_args.args[0] == settings_obj.image_cropped
        save_mock.assert_called_once()

    def test_process_task_clears_webp_when_no_source_image(self, mocker: MockerFixture) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_jpeg_field("background-source.jpg"),
            title="Shop",
        )
        settings_obj.image = None
        settings_obj.image_cropped = None

        save_mock = mocker.patch.object(ShopSettings, "save")

        process_image_task("shop", "ShopSettings", settings_obj.pk, ["image"])

        save_mock.assert_called_once()
