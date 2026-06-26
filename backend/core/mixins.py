from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, ClassVar, cast

from django.db import models
from django.db.models import QuerySet
from django.db.models.base import ModelBase
from django.db.models.fields.files import ImageFieldFile

from common.types import ImageVariantSource, ImageVariantSpec
from common.utils.image import (
    IMAGE_FORMAT,
    build_image_variant_file_path,
    build_image_with_given_width,
    file_exists_in_storage,
)

type ImageVariantTarget = tuple[str, int, int]


class DjangoModelABCMeta(ModelBase, ABCMeta):
    """Combine Django's model metaclass with ``ABCMeta`` for abstract model mixins."""


class ImageVariantModelMixin(metaclass=DjangoModelABCMeta):
    """Shared runtime and contract for Django models using ImageVariant syncing."""

    image_variant_specs: ClassVar[tuple[ImageVariantSpec, ...]] = ()

    @abstractmethod
    def get_image_variant_sources(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageVariantSource]:
        """Return the model-to-mixin contract for variant generation sources.

        This does not return concrete variants. It returns the original/source
        image families that the shared mixin should read from storage. The mixin
        later asks ``get_image_variant_specs()`` for the model's concrete
        ``role + width + quality`` targets before creating ``ImageVariant`` rows.

        Args:
            changed_field_names: Optional list of logical image field names that
                changed on the model and therefore need syncing.

        Returns:
            Source definitions containing the model field name, effective source
            file, upload directory, and optional role namespace.
        """
        raise NotImplementedError

    def get_image_variant_specs(self) -> tuple[ImageVariantSpec, ...]:
        """Return generated variant specs for this model."""
        return self.image_variant_specs

    def make_thumbnail(self) -> bool:
        """Create thumbnail ImageVariant rows from configured model specs."""
        created_count = 0
        for source in self.get_image_variant_sources():
            targets = self._get_thumbnail_variant_targets(source)
            if not targets:
                continue
            target_roles = {role for role, _width, _quality in targets}
            target_widths = {width for _role, width, _quality in targets}
            cast(Any, self).variants.filter(
                role__in=target_roles,
                width__in=target_widths,
            ).delete()
            created_count += self._generate_image_variants_for_source(source, targets).count()
        return created_count > 0

    def _get_thumbnail_variant_targets(
        self,
        source: ImageVariantSource,
    ) -> tuple[ImageVariantTarget, ...]:
        targets: list[ImageVariantTarget] = []
        for spec in self.get_image_variant_specs():
            if spec.role != "thumbnail":
                continue
            stored_role = self._build_variant_role(spec.role, source.role_namespace)
            targets.extend(
                (stored_role, width, spec.quality) for width in spec.viewport_widths.as_tuple()
            )
        return tuple(targets)

    def sync_image_variants(
        self,
        changed_field_names: list[str] | None = None,
        *,
        force: bool = False,
    ) -> int:
        """Synchronize all configured variant families for this model instance.

        ``changed_field_names`` limits syncing to specific source families when a
        task was triggered by a targeted field change. ``force`` performs a full
        rebuild for every selected family, replacing current rows only after all
        replacements are generated successfully.
        """
        changed_variant_count = 0
        effective_force = force or changed_field_names is not None
        for source in self.get_image_variant_sources(changed_field_names):
            changed_variant_count += self._sync_variants_for_source(source, force=effective_force)
        return changed_variant_count

    required_variant_roles = frozenset({"background", "original_format", "thumbnail"})

    def has_pending_image_variant_sync(self, changed_field_names: list[str] | None = None) -> bool:
        """Return whether any selected source family is out of sync with storage.

        This is used by backfills and diagnostics to answer "would syncing this
        object change anything?" without actually deleting or generating files.
        """
        for source in self.get_image_variant_sources(changed_field_names):
            variant_queryset = self._get_variant_queryset_for_source(source)
            if not source.source_image:
                if variant_queryset.exists():
                    return True
                continue

            variants_to_generate, variants_to_delete = self._get_image_variant_sync_plan(source)
            if variants_to_generate or variants_to_delete.exists():
                return True

        return False

    def _sync_variants_for_source(self, source: ImageVariantSource, *, force: bool) -> int:
        """Synchronize one source family and return the number of changed rows.

        A source family represents one canonical input image plus the variant
        spec set derived from it, for example ``BaseImage.original`` or
        ``User.avatar``. Missing sources clear stale rows; forced sync rebuilds
        everything for that family; incremental sync only fixes drift.
        """
        variant_queryset = self._get_variant_queryset_for_source(source)
        if not source.source_image:
            deleted_count, _ = variant_queryset.delete()
            return deleted_count

        if force:
            deleted_count, _ = variant_queryset.delete()
            generated_count = int(
                self._generate_image_variants_for_source(
                    source,
                    self._get_expected_image_variant_targets(source),
                ).count()
            )
            return int(deleted_count) + generated_count

        variants_to_generate, variants_to_delete = self._get_image_variant_sync_plan(source)
        deleted_count, _ = variants_to_delete.delete()
        generated_count = int(
            self._generate_image_variants_for_source(
                source,
                variants_to_generate,
            ).count()
        )
        return deleted_count + generated_count

    @staticmethod
    def _build_variant_role(role: str, source_name: str | None = None) -> str:
        """Return the stored role key, optionally namespaced by source family."""
        if source_name:
            return f"{source_name}__{role}"
        return role

    def _get_variant_queryset_for_source(self, source: ImageVariantSource) -> models.QuerySet[Any]:
        """Return the variant rows owned by exactly one source family."""
        variants: QuerySet = self.variants.all()  # type: ignore[attr-defined]
        if source.role_namespace:
            return variants.filter(role__startswith=f"{source.role_namespace}__")
        return variants

    def _get_image_variant_sync_plan(
        self, source: ImageVariantSource
    ) -> tuple[tuple[ImageVariantTarget, ...], models.QuerySet[Any]]:
        """Plan incremental sync for one source family.

        Returns:
        - variant specs that are still missing and should be generated
        - existing rows that are stale, unsupported, or point at empty files
        """
        expected_targets = self._get_expected_image_variant_targets(source)
        expected_keys = {(role, width) for role, width, _quality in expected_targets}
        existing_variants = list(self._get_variant_queryset_for_source(source))
        valid_existing_keys = {
            (variant.role, variant.width)
            for variant in existing_variants
            if (
                (variant.role, variant.width) in expected_keys
                and variant.file.name
                and file_exists_in_storage(variant.file)
            )
        }
        variant_ids_to_delete = [
            variant.pk
            for variant in existing_variants
            if (
                (variant.role, variant.width) not in expected_keys
                or not variant.file.name
                or not file_exists_in_storage(variant.file)
            )
        ]
        missing_keys = expected_keys - valid_existing_keys
        variants_to_generate = tuple(
            target for target in expected_targets if (target[0], target[1]) in missing_keys
        )
        variants_to_delete: models.QuerySet[Any] = self.variants.filter(  # type: ignore[attr-defined] # noqa: E501
            pk__in=variant_ids_to_delete
        )
        return variants_to_generate, variants_to_delete

    def _get_expected_image_variant_targets(
        self, source: ImageVariantSource
    ) -> tuple[ImageVariantTarget, ...]:
        """Return source-supported ``(role, width, quality)`` generation targets.

        Variant widths are defined by the model's ``ImageVariantSpec`` entries.
        The source image width is only a no-upscale guard: configured role widths
        larger than the source are removed. Required roles such as ``thumbnail``
        collapse to the source width instead of disappearing entirely for small
        images.
        """
        source_width = self._get_source_width(source.source_image)
        if source_width is None:
            return ()

        expected_targets: list[ImageVariantTarget] = []
        for spec in self.get_image_variant_specs():
            stored_role = self._build_variant_role(spec.role, source.role_namespace)
            widths = spec.target_widths_for_source(
                source_width,
                required=spec.role in self.required_variant_roles,
            )
            expected_targets.extend((stored_role, width, spec.quality) for width in widths)
        return tuple(expected_targets)

    def _generate_image_variants_for_source(
        self,
        source: ImageVariantSource,
        targets: tuple[ImageVariantTarget, ...],
    ) -> models.QuerySet[Any]:
        """Generate concrete ImageVariant rows for explicit role/width targets."""
        from core.models import ImageVariant

        generated_variant_ids: list[Any] = []
        source_image = source.source_image
        if not source_image:
            return cast("models.QuerySet[ImageVariant]", cast(Any, self).variants.none())

        failed_targets: list[ImageVariantTarget] = []
        for role, width, quality in targets:
            with source_image.open("rb") as opened_source:
                result = build_image_with_given_width(
                    opened_source,
                    width=width,
                    quality=quality,
                    filename_prefix=f"{role}_{width}_",
                )
            if result is None:
                failed_targets.append((role, width, quality))
                continue

            content, generated_width, generated_height = result
            content_name = content.name
            if content_name is None:
                raise ValueError(f"Generated image variant for {role}:{width} has no filename")

            path = build_image_variant_file_path(
                upload_dir=source.upload_dir,
                role=role,
                filename=content_name,
                role_namespace=source.role_namespace,
            )
            variant = ImageVariant(
                image=self,
                role=role,
                width=generated_width,
                height=generated_height,
                mime_type=IMAGE_FORMAT.mime_type,
            )
            variant.file.save(
                path,
                content,
            )
            generated_variant_ids.append(variant.pk)

        if failed_targets:
            if generated_variant_ids:
                cast(Any, self).variants.filter(pk__in=generated_variant_ids).delete()
            failed_labels = ", ".join(f"{role}:{width}" for role, width, _quality in failed_targets)
            raise ValueError(
                "Failed to generate image variant(s) "
                f"for source {getattr(source_image, 'name', '')}: {failed_labels}"
            )

        return cast(
            "models.QuerySet[ImageVariant]",
            cast(Any, self).variants.filter(pk__in=generated_variant_ids),
        )

    @staticmethod
    def _get_source_width(source: ImageFieldFile | None) -> int | None:
        """Return the stored source width, or raise when the named file is missing."""
        if not source:
            return None
        if file_exists_in_storage(source):
            try:
                return source.width
            except (OSError, ValueError) as exc:
                raise ValueError(
                    f"Unable to read source image dimensions: {getattr(source, 'name', '')}"
                ) from exc
        return None

    def get_variant_file(
        self,
        role: str,
        width: int,
        *,
        source_name: str | None = None,
    ) -> ImageFieldFile | None:
        """Return one stored variant file by role, width, and optional source family."""
        stored_role = self._build_variant_role(role, source_name)
        variants = self.variants.filter(  # type: ignore[attr-defined]
            role=stored_role,
            width=width,
        ).exclude(file="")
        for variant in variants:
            if file_exists_in_storage(variant.file):
                return cast(ImageFieldFile, variant.file)
        return None

    def get_variant_image_url(self, role: str, width: int) -> str | None:
        """Return the public URL for one generated variant role when it exists."""
        return self.get_variant_url(role, width)

    def get_variant_url(
        self,
        role: str,
        width: int,
        *,
        source_name: str | None = None,
    ) -> str | None:
        """Return the public URL for one generated variant role and width when it exists."""
        image_file = self.get_variant_file(
            role,
            width,
            source_name=source_name,
        )
        if image_file:
            return str(image_file.url)
        return None

    def get_available_variant_url(
        self,
        role: str,
        *,
        preferred_width: int | None = None,
        source_name: str | None = None,
    ) -> str | None:
        """Return an existing variant URL for a role, preferring an exact width."""
        if preferred_width is not None:
            variant_url = self.get_variant_url(
                role,
                preferred_width,
                source_name=source_name,
            )
            if variant_url:
                return variant_url

        stored_role = self._build_variant_role(role, source_name)
        variants = (
            cast(Any, self).variants.filter(role=stored_role).exclude(file="").order_by("-width")
        )
        for variant in variants:
            if file_exists_in_storage(variant.file):
                return str(variant.file.url)
        return None
