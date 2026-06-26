from io import BytesIO
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from PIL import Image

from astrophotography.serializers import AstroImageSerializerList
from astrophotography.tests.factories import AstroImageFactory, MainPageBackgroundImageFactory
from common.tests.image_helpers import jpeg_field
from common.types import ImageVariantSource, ImageVariantSpec, ViewportWidths
from core.mixins import ImageVariantModelMixin
from core.models import BaseImage, ImageVariant
from core.tasks import process_image_task
from programming.tests.factories import ProjectImageFactory
from shop.models import ShopSettings
from shop.tests.factories import ShopProductFactory
from users.tests.factories import UserFactory


def _stored_webp_size(image, name: str) -> tuple[int, int]:
    with image.original.storage.open(name, "rb") as stored_file:
        with Image.open(BytesIO(stored_file.read())) as generated:
            return generated.size


@pytest.mark.django_db
class TestImageVariantFileDeletion:
    def test_delete_file_uses_field_file_delete_without_model_save(self) -> None:
        variant = ImageVariant()
        file_mock = MagicMock()
        file_mock.__bool__.return_value = True
        variant.file = file_mock

        variant.delete_file()

        file_mock.delete.assert_called_once_with(save=False)

    def test_parent_instance_delete_removes_variant_files(self) -> None:
        image = AstroImageFactory(original=jpeg_field("owner-delete.jpg", size=(1200, 800)))
        variant = ImageVariant.objects.create(
            image=image,
            role="cleanup_probe",
            width=1,
            height=1,
            mime_type="image/webp",
        )
        variant.file.save("owner-instance-delete.webp", jpeg_field("variant.jpg"), save=True)
        storage = variant.file.storage
        variant_name = variant.file.name

        assert storage.exists(variant_name)

        image.delete()

        assert not storage.exists(variant_name)

    @pytest.mark.parametrize(
        "owner_factory",
        [
            lambda: AstroImageFactory(original=jpeg_field("owner-astro.jpg", size=(1200, 800))),
            lambda: MainPageBackgroundImageFactory(
                original=jpeg_field("owner-background.jpg", size=(1200, 800))
            ),
            lambda: ProjectImageFactory(original=jpeg_field("owner-project.jpg", size=(1200, 800))),
            ShopProductFactory,
            lambda: ShopSettings.objects.create(
                title="Shop",
                image=jpeg_field("owner-shop-settings.jpg", size=(1200, 800)),
            ),
            lambda: UserFactory(avatar=jpeg_field("owner-user.jpg", size=(800, 800))),
        ],
    )
    def test_parent_queryset_delete_removes_variant_files(self, owner_factory) -> None:
        owner = owner_factory()
        variant = ImageVariant.objects.create(
            image=owner,
            role="cleanup_probe",
            width=1,
            height=1,
            mime_type="image/webp",
        )
        variant.file.save("owner-queryset-delete.webp", jpeg_field("variant.jpg"), save=True)
        storage = variant.file.storage
        variant_name = variant.file.name

        assert storage.exists(variant_name)

        type(owner).objects.filter(pk=owner.pk).delete()

        assert not storage.exists(variant_name)


class TestImageVariantSpec:
    def test_spec_names_variant_role_viewport_widths_quality_and_label(self) -> None:
        spec = ImageVariantSpec(
            role="card",
            viewport_widths=ViewportWidths(
                mobile=320,
                tablet=560,
                desktop=840,
                wide=1120,
            ),
            quality=90,
            label="Astrophotography card/grid candidates",
        )

        assert spec.role == "card"
        assert spec.viewport_widths.as_tuple() == (320, 560, 840, 1120)
        assert spec.quality == 90
        assert spec.label == "Astrophotography card/grid candidates"

    def test_viewport_widths_can_use_one_width_for_every_viewport(self) -> None:
        widths = ViewportWidths.fixed(560)

        assert widths == ViewportWidths(
            mobile=560,
            tablet=560,
            desktop=560,
            wide=560,
        )

    def test_spec_filters_target_widths_by_source_width(self) -> None:
        spec = ImageVariantSpec(
            role="card",
            viewport_widths=ViewportWidths(
                mobile=320,
                tablet=560,
                desktop=840,
                wide=1120,
            ),
            quality=90,
        )

        assert spec.target_widths_for_source(900) == (320, 560, 840)

    def test_required_spec_uses_source_width_when_source_is_smaller_than_targets(self) -> None:
        spec = ImageVariantSpec(
            role="thumbnail",
            viewport_widths=ViewportWidths.fixed(560),
            quality=100,
        )

        assert spec.target_widths_for_source(100, required=True) == (100,)


class TestImageVariantMixinCompatibility:
    class ImageOwner(ImageVariantModelMixin):
        def get_image_variant_sources(
            self, changed_field_names: list[str] | None = None
        ) -> list[ImageVariantSource]:
            return []

        def get_image_variant_specs(self) -> tuple[ImageVariantSpec, ...]:
            return (
                ImageVariantSpec(
                    role="thumbnail",
                    viewport_widths=ViewportWidths.fixed(560),
                    quality=100,
                ),
            )

    class ResponsiveThumbnailOwner(ImageVariantModelMixin):
        def get_image_variant_sources(
            self, changed_field_names: list[str] | None = None
        ) -> list[ImageVariantSource]:
            return []

        def get_image_variant_specs(self) -> tuple[ImageVariantSpec, ...]:
            return (
                ImageVariantSpec(
                    role="thumbnail",
                    viewport_widths=ViewportWidths(
                        mobile=320,
                        tablet=560,
                        desktop=840,
                        wide=1120,
                    ),
                    quality=100,
                ),
            )

    class NoThumbnailOwner(ImageVariantModelMixin):
        def get_image_variant_sources(
            self, changed_field_names: list[str] | None = None
        ) -> list[ImageVariantSource]:
            return []

        def get_image_variant_specs(self) -> tuple[ImageVariantSpec, ...]:
            return ()

    def test_make_thumbnail_compatibility_method_lives_on_variant_mixin(self) -> None:
        assert "thumbnail" not in BaseImage._meta.fields_map
        assert "thumbnail" not in {field.name for field in BaseImage._meta.fields}
        assert "make_thumbnail" in ImageVariantModelMixin.__dict__
        assert "make_thumbnail" not in BaseImage.__dict__

    def test_make_thumbnail_creates_fixed_thumbnail_variant_spec_width(self) -> None:
        owner = self.ImageOwner()
        source = ImageVariantSource(
            field_name="original",
            source_image=MagicMock(),
            upload_dir="images",
        )
        owner.get_image_variant_sources = MagicMock(  # type: ignore[method-assign]
            return_value=[source]
        )
        variants = MagicMock()
        owner.variants = variants
        generated = MagicMock()
        generated.count.return_value = 1
        owner._generate_image_variants_for_source = MagicMock(  # type: ignore[method-assign]
            return_value=generated
        )

        assert owner.make_thumbnail() is True

        variants.filter.assert_called_once_with(role__in={"thumbnail"}, width__in={560})
        variants.filter.return_value.delete.assert_called_once_with()
        owner._generate_image_variants_for_source.assert_called_once_with(
            source,
            (("thumbnail", 560, 100),),
        )

    def test_make_thumbnail_creates_all_thumbnail_variant_spec_widths(self) -> None:
        owner = self.ResponsiveThumbnailOwner()
        source = ImageVariantSource(
            field_name="original",
            source_image=MagicMock(),
            upload_dir="images",
        )
        owner.get_image_variant_sources = MagicMock(  # type: ignore[method-assign]
            return_value=[source]
        )
        variants = MagicMock()
        owner.variants = variants
        generated = MagicMock()
        generated.count.return_value = 4
        owner._generate_image_variants_for_source = MagicMock(  # type: ignore[method-assign]
            return_value=generated
        )

        assert owner.make_thumbnail() is True

        variants.filter.assert_called_once_with(
            role__in={"thumbnail"},
            width__in={320, 560, 840, 1120},
        )
        variants.filter.return_value.delete.assert_called_once_with()
        owner._generate_image_variants_for_source.assert_called_once_with(
            source,
            (
                ("thumbnail", 320, 100),
                ("thumbnail", 560, 100),
                ("thumbnail", 840, 100),
                ("thumbnail", 1120, 100),
            ),
        )

    def test_make_thumbnail_returns_false_without_thumbnail_variant_spec(self) -> None:
        owner = self.NoThumbnailOwner()
        owner.get_image_variant_sources = MagicMock(  # type: ignore[method-assign]
            return_value=[
                ImageVariantSource(
                    field_name="original",
                    source_image=MagicMock(),
                    upload_dir="images",
                )
            ]
        )

        assert owner.make_thumbnail() is False


@pytest.mark.django_db
class TestBaseImageVariants:
    def test_process_image_task_generates_astroimage_original_format_variant_like_legacy_webp(
        self,
    ) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("legacy-original.jpg", size=(3000, 2000)),
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
                original=jpeg_field("nebula.jpg", size=(1200, 800)),
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

    def test_process_image_task_generates_required_variants_for_small_sources(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("tiny.jpg", size=(100, 100)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)

        image.refresh_from_db()
        original_format = image.variants.get(role="original_format")
        thumbnail_variant = image.variants.get(role="thumbnail")

        assert original_format.width == 100
        assert original_format.height == 100
        assert thumbnail_variant.width == 100
        assert thumbnail_variant.height == 100
        assert image.get_image_url("thumbnail", 100) == thumbnail_variant.file.url

    def test_main_page_background_generates_hero_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = MainPageBackgroundImageFactory(
                original=jpeg_field("milky-way.jpg", size=(2600, 1734)),
            )

        process_image_task("astrophotography", "MainPageBackgroundImage", image.pk)

        image.refresh_from_db()
        hero_widths = [
            variant.width for variant in image.variants.filter(role="hero").order_by("width")
        ]
        original_format_count = image.variants.filter(role="original_format").count()
        assert hero_widths == [
            1280,
            1920,
            2560,
        ]
        assert original_format_count == 0

    def test_variant_filenames_change_when_source_file_changes(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("first.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        first_names = {variant.file.name for variant in image.variants.filter(role="card")}

        with patch("core.models.process_image_task.delay_on_commit"):
            image.original = jpeg_field("second.jpg", size=(1200, 800))
            image.save()

        process_image_task("astrophotography", "AstroImage", image.pk, ["original"])
        image.refresh_from_db()
        second_names = {variant.file.name for variant in image.variants.filter(role="card")}

        assert second_names
        assert first_names.isdisjoint(second_names)

    def test_generates_only_missing_variants_without_force(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("missing-only.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        existing_by_width = {
            variant.width: variant.file.name
            for variant in image.variants.filter(role="card").order_by("width")
        }
        image.variants.filter(role="card", width=560).delete()

        changed_variant_count = image.sync_image_variants(force=False)

        image.refresh_from_db()
        updated_by_width = {
            variant.width: variant.file.name
            for variant in image.variants.filter(role="card").order_by("width")
        }
        assert changed_variant_count == 1
        assert updated_by_width[320] == existing_by_width[320]
        assert updated_by_width[840] == existing_by_width[840]
        assert updated_by_width[1120] == existing_by_width[1120]
        assert updated_by_width[560] != existing_by_width[560]

    def test_has_pending_image_variant_sync_tracks_missing_and_stale_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("pending-sync.jpg", size=(1200, 800)),
            )

        assert image.has_pending_image_variant_sync() is True

        changed_variant_count = image.sync_image_variants(force=False)

        assert changed_variant_count > 0
        assert image.has_pending_image_variant_sync() is False

        thumbnail_variant = image.variants.get(role="thumbnail", width=560)
        image.original.storage.delete(thumbnail_variant.file.name)

        assert image.has_pending_image_variant_sync() is True

    def test_sync_image_variants_clears_stale_variants_when_source_is_missing(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("missing-source-clear.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        variant_names = [variant.file.name for variant in image.variants.all()]
        image.original.storage.delete(image.original.name)

        changed_variant_count = image.sync_image_variants(force=False)

        image.refresh_from_db()
        assert changed_variant_count == len(variant_names)
        assert image.variants.count() == 0
        assert all(not image.original.storage.exists(name) for name in variant_names)

    def test_rebuilds_stale_variant_files_without_force(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("stale-source-file.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()

        thumbnail_variant = image.variants.get(role="thumbnail", width=560)
        old_file_name = thumbnail_variant.file.name
        image.original.storage.delete(old_file_name)
        assert not image.original.storage.exists(old_file_name)

        changed_variant_count = image.sync_image_variants(force=False)

        image.refresh_from_db()
        new_thumbnail = image.variants.get(role="thumbnail", width=560)
        assert changed_variant_count >= 2
        assert new_thumbnail.file.name != old_file_name
        assert image.original.storage.exists(new_thumbnail.file.name)

    def test_deletes_stale_variants_without_recreating_valid_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("stale-only.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        existing_names = {
            variant.file.name for variant in image.variants.filter(role="card").order_by("width")
        }
        stale_content = jpeg_field("stale-extra.jpg", size=(1200, 800))
        stale_name = image.original.storage.save("images/card/stale-extra.webp", stale_content)
        stale_variant = image.variants.create(
            file=stale_name,
            role="card",
            width=999,
            height=666,
            mime_type="image/webp",
        )

        changed_variant_count = image.sync_image_variants(force=False)

        image.refresh_from_db()
        assert changed_variant_count == 1
        assert not image.variants.filter(pk=stale_variant.pk).exists()
        assert not image.original.storage.exists(stale_name)
        assert {
            variant.file.name for variant in image.variants.filter(role="card").order_by("width")
        } == existing_names

    def test_force_rebuilds_all_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("force.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        first_names = {variant.file.name for variant in image.variants.filter(role="card")}

        changed_variant_count = image.sync_image_variants(force=True)

        image.refresh_from_db()
        second_names = {variant.file.name for variant in image.variants.filter(role="card")}
        assert changed_variant_count >= 4
        card_widths = [
            variant.width for variant in image.variants.filter(role="card").order_by("width")
        ]
        assert card_widths == [
            320,
            560,
            840,
            1120,
        ]
        assert first_names.isdisjoint(second_names)
        assert all(not image.original.storage.exists(name) for name in first_names)

    def test_force_clears_existing_variants_before_rebuild_failure(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("force-failure.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        existing_names = {variant.file.name for variant in image.variants.order_by("role", "width")}

        with (
            patch("core.mixins.build_image_with_given_width", return_value=None),
            pytest.raises(ValueError, match="Failed to generate image variant"),
        ):
            image.sync_image_variants(force=True)

        image.refresh_from_db()
        assert image.variants.count() == 0
        assert all(not image.original.storage.exists(name) for name in existing_names)

    def test_variant_instance_delete_removes_stored_file(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("delete-instance.jpg", size=(1200, 800)),
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
                original=jpeg_field("delete-files.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        variant_names = [variant.file.name for variant in image.variants.filter(role="card")]

        deleted_count, deleted_by_model = image.variants.filter(role="card").delete()

        assert deleted_count == 4
        assert deleted_by_model == {"core.ImageVariant": 4}
        assert image.variants.filter(role="card").count() == 0
        assert all(not image.original.storage.exists(name) for name in variant_names)

    def test_project_image_specs_create_original_format_variant(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = ProjectImageFactory(
                original=jpeg_field("project.jpg", size=(1200, 800)),
            )

        process_image_task("programming", "ProjectImage", image.pk)

        image.refresh_from_db()
        assert [spec.role for spec in image.get_image_variant_specs()] == ["original_format"]
        original_format = image.variants.get(role="original_format")
        assert original_format.width == 1200
        assert original_format.height == 800

    def test_list_serializer_keeps_legacy_thumbnail_url(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("thumbnail.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()

        data = AstroImageSerializerList(image).data

        assert data["thumbnail_url"]
        assert "image_variants" not in data

    def test_get_image_url_returns_generated_thumbnail_variant(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("thumbnail-url.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        variant = image.variants.get(role="thumbnail", width=560)

        assert image.get_image_url("thumbnail", 560) == variant.file.url

    def test_get_available_variant_url_prefers_exact_width_then_largest_existing_width(
        self,
    ) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("available-card.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        exact_variant = image.variants.get(role="card", width=560)
        largest_variant = image.variants.get(role="card", width=1120)

        assert (
            image.get_available_variant_url("card", preferred_width=560) == exact_variant.file.url
        )
        assert (
            image.get_available_variant_url("card", preferred_width=999) == largest_variant.file.url
        )

    def test_get_image_url_falls_back_when_thumbnail_variant_is_missing(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("thumbnail-missing.jpg", size=(1200, 800)),
            )

        process_image_task("astrophotography", "AstroImage", image.pk)
        image.refresh_from_db()
        image.variants.filter(role="thumbnail").delete()

        assert image.get_image_url("thumbnail", 560) == image.original.url

    def test_namespaced_variant_sources_sync_only_requested_changed_fields(self) -> None:
        with patch("users.models.process_image_task.delay_on_commit"):
            user = UserFactory.create_superuser()
            user.avatar = jpeg_field("avatar.jpg", size=(800, 800))
            user.about_me_image = jpeg_field("portrait.jpg", size=(900, 900))
            user.save()

        avatar_count = user.sync_image_variants(["avatar"], force=False)

        user.refresh_from_db()
        avatar_variant = user.variants.get(role="avatar__original_format", width=800)
        assert avatar_count == 1
        assert avatar_variant.file.name.startswith("avatars/avatar/original_format/")
        assert not user.variants.filter(role="about_me_image__original_format").exists()
        assert (
            user.get_variant_url("original_format", 800, source_name="avatar")
            == avatar_variant.file.url
        )
        assert user.get_variant_url("original_format", 800) is None

        portrait_count = user.sync_image_variants(["about_me_image"], force=False)

        user.refresh_from_db()
        portrait_variant = user.variants.get(role="about_me_image__original_format", width=900)
        assert portrait_count == 1
        assert portrait_variant.file.name.startswith(
            "about_me_images/about_me_image/original_format/"
        )

    def test_source_width_raises_when_existing_file_dimensions_cannot_be_read(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("bad-dimensions.jpg", size=(1200, 800)),
            )
        source = MagicMock()
        source.name = "images/bad-dimensions.jpg"
        type(source).width = PropertyMock(side_effect=OSError("cannot read dimensions"))

        with (
            patch("core.mixins.file_exists_in_storage", return_value=True),
            pytest.raises(ValueError, match="Unable to read source image dimensions"),
        ):
            image._get_source_width(source)
