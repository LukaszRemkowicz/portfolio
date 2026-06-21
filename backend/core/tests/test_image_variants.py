from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from astrophotography.serializers import AstroImageSerializerList
from astrophotography.tests.factories import AstroImageFactory, MainPageBackgroundImageFactory
from common.tests.image_helpers import _jpeg_field
from common.types import ImageVariantSpec
from core.models import ImageVariant
from core.tasks import process_image_task
from programming.tests.factories import ProjectImageFactory


def _stored_webp_size(image, name: str) -> tuple[int, int]:
    with image.original.storage.open(name, "rb") as stored_file:
        with Image.open(BytesIO(stored_file.read())) as generated:
            return generated.size


class TestImageVariantFileDeletion:
    def test_delete_file_uses_field_file_delete_without_model_save(self) -> None:
        variant = ImageVariant()
        file_mock = MagicMock()
        file_mock.__bool__.return_value = True
        variant.file = file_mock

        variant.delete_file()

        file_mock.delete.assert_called_once_with(save=False)


class TestImageVariantSpec:
    def test_spec_names_variant_widths_quality_and_label(self) -> None:
        spec = ImageVariantSpec(
            role="card",
            widths=(320, 560, 840, 1120),
            quality=90,
            label="Astrophotography card/grid candidates",
        )

        assert spec.role == "card"
        assert spec.widths == (320, 560, 840, 1120)
        assert spec.quality == 90
        assert spec.label == "Astrophotography card/grid candidates"


@pytest.mark.django_db
class TestBaseImageVariants:
    def test_process_image_task_generates_original_format_variant_from_legacy_spec(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("legacy-original.jpg", size=(3000, 2000)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)

        image.refresh_from_db()
        original_format = image.variants.get(role="original_format")
        assert original_format.width == 1920
        assert original_format.height == 1280
        assert original_format.mime_type == "image/webp"
        assert original_format.file.name.startswith("images/original_format/")
        assert _stored_webp_size(image, original_format.file.name) == (1920, 1280)

    def test_process_image_task_generates_responsive_variants_preserving_aspect_ratio(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("nebula.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)

        image.refresh_from_db()
        card_variants = list(image.variants.filter(role="card").order_by("width"))
        detail_variants = list(image.variants.filter(role="detail").order_by("width"))
        thumbnail_variant = image.variants.get(role="thumbnail")
        assert [variant.width for variant in card_variants] == [320, 560, 840, 1120]
        assert [variant.height for variant in card_variants] == [213, 373, 560, 747]
        assert [variant.width for variant in detail_variants] == []
        assert thumbnail_variant.width == 560
        assert thumbnail_variant.height == 373
        assert thumbnail_variant.file.name.startswith("images/thumbnail/")
        assert {variant.mime_type for variant in card_variants} == {"image/webp"}
        assert all(variant.file.name.startswith("images/card/") for variant in card_variants)

        for variant in card_variants:
            assert _stored_webp_size(image, variant.file.name) == (
                variant.width,
                variant.height,
            )

    def test_main_page_background_generates_hero_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = MainPageBackgroundImageFactory(
                original=_jpeg_field("milky-way.jpg", size=(2600, 1734)),
            )

        process_image_task("astrophotography", "MainPageBackgroundImage", image.pk)

        image.refresh_from_db()
        hero_widths = [
            variant.width for variant in image.variants.filter(role="hero").order_by("width")
        ]
        assert hero_widths == [
            1280,
            1920,
            2560,
        ]

    def test_variant_filenames_change_when_source_file_changes(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("first.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        first_names = {variant.file.name for variant in image.variants.filter(role="card")}

        with patch("core.models.process_image_task.delay_on_commit"):
            image.original = _jpeg_field("second.jpg", size=(1200, 800))
            image.save()

        process_image_task("astrophotography", "AstroImage", image.pk, ["original"])
        image.refresh_from_db()
        second_names = {variant.file.name for variant in image.variants.filter(role="card")}

        assert second_names
        assert first_names.isdisjoint(second_names)

    def test_generates_only_missing_variants_without_force(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("missing-only.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        existing_by_width = {
            variant.width: variant.file.name
            for variant in image.variants.filter(role="card").order_by("width")
        }
        image.variants.filter(role="card", width=560).delete()

        generated = image.generate_image_variants_or_none()

        image.refresh_from_db()
        updated_by_width = {
            variant.width: variant.file.name
            for variant in image.variants.filter(role="card").order_by("width")
        }
        assert [variant.width for variant in generated or []] == [560]
        assert updated_by_width[320] == existing_by_width[320]
        assert updated_by_width[840] == existing_by_width[840]
        assert updated_by_width[1120] == existing_by_width[1120]
        assert updated_by_width[560] != existing_by_width[560]

    def test_deletes_stale_variants_without_recreating_valid_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("stale-only.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        existing_names = {
            variant.file.name for variant in image.variants.filter(role="card").order_by("width")
        }
        stale_content = _jpeg_field("stale-extra.jpg", size=(1200, 800))
        stale_name = image.original.storage.save("images/card/stale-extra.webp", stale_content)
        stale_variant = image.variants.create(
            file=stale_name,
            role="card",
            width=999,
            height=666,
            mime_type="image/webp",
        )

        generated = image.generate_image_variants_or_none()

        image.refresh_from_db()
        assert generated is not None
        assert not generated.exists()
        assert not image.variants.filter(pk=stale_variant.pk).exists()
        assert not image.original.storage.exists(stale_name)
        assert {
            variant.file.name for variant in image.variants.filter(role="card").order_by("width")
        } == existing_names

    def test_force_rebuilds_all_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("force.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        first_names = {variant.file.name for variant in image.variants.filter(role="card")}

        generated = image.generate_image_variants_or_none(force=True)

        image.refresh_from_db()
        second_names = {variant.file.name for variant in image.variants.filter(role="card")}
        generated_cards = (generated or image.variants.none()).filter(role="card")
        assert [variant.width for variant in generated_cards] == [320, 560, 840, 1120]
        assert first_names.isdisjoint(second_names)
        assert all(not image.original.storage.exists(name) for name in first_names)

    def test_variant_instance_delete_removes_stored_file(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("delete-instance.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        variant = image.variants.filter(role="card", width=320).get()
        variant_name = variant.file.name

        deleted_count, deleted_by_model = variant.delete()

        assert deleted_count == 1
        assert deleted_by_model == {"core.ImageVariant": 1}
        assert not image.variants.filter(pk=variant.pk).exists()
        assert not image.original.storage.exists(variant_name)

    def test_variant_queryset_delete_removes_stored_files(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("delete-files.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        variant_names = [variant.file.name for variant in image.variants.filter(role="card")]

        deleted_count, deleted_by_model = image.variants.filter(role="card").delete()

        assert deleted_count == 4
        assert deleted_by_model == {"core.ImageVariant": 4}
        assert image.variants.filter(role="card").count() == 0
        assert all(not image.original.storage.exists(name) for name in variant_names)

    def test_project_image_without_variant_specs_does_not_create_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = ProjectImageFactory(
                original=_jpeg_field("project.jpg", size=(1200, 800)),
            )

        process_image_task("programming", "ProjectImage", image.pk)

        image.refresh_from_db()
        assert image.get_image_variant_specs() == ()
        assert image.variants.count() == 0

    def test_list_serializer_keeps_legacy_thumbnail_url(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=_jpeg_field("thumbnail.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()

        data = AstroImageSerializerList(image).data

        assert data["thumbnail_url"]
        assert "image_variants" not in data
