from decimal import Decimal
from unittest.mock import patch

import pytest

from django.core.exceptions import ValidationError

from common.tests.image_helpers import jpeg_field, png_field
from programming.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestProject:
    def test_paid_requires_positive_price(self):
        project = ProjectFactory.build(pricing="paid", price=None)
        with pytest.raises(ValidationError) as exc:
            project.clean()
        assert "price" in exc.value.message_dict
        project.price = Decimal("49")
        project.clean()

    def test_non_paid_drops_price_on_save(self):
        project = ProjectFactory(pricing="free", price=Decimal("5"))
        project.refresh_from_db()
        assert project.price is None

    def test_str(self):
        assert str(ProjectFactory(name="Alpha Project")) == "Alpha Project"

    def test_new_source_resets_crop_and_submits_processing(self):
        with patch("programming.models.submit"):
            project = ProjectFactory(image_cropped=png_field("crop.png", size=(1600, 1000)))
        assert project.image_cropped

        with patch("programming.models.submit") as submit:
            project.image = jpeg_field("new-source.jpg")
            project.save()

        assert not project.image_cropped
        submit.assert_called_once()

    def test_cropped_image_is_variant_source(self):
        with patch("programming.models.submit"):
            project = ProjectFactory(image_cropped=png_field("crop.png", size=(1600, 1000)))
        assert project.get_image_variant_sources()[0].source_image == project.image_cropped


@pytest.mark.django_db
def test_translate_project_delegates_to_translate_model():
    from translation.services import TranslationService

    service = TranslationService.__new__(TranslationService)
    with patch.object(TranslationService, "translate_model", return_value=({}, {})) as mocked:
        assert service.translate_project("obj", "pl", force=True) == ({}, {})
    mocked.assert_called_once_with("obj", "pl", True)
