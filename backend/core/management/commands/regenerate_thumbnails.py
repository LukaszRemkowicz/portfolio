"""Regenerate thumbnail ImageVariant rows for thumbnail-producing models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields.files import FieldFile

from astrophotography.models import AstroImage
from common.utils.image import file_exists_in_storage
from shop.models import ShopProduct


@dataclass(frozen=True)
class ThumbnailTarget:
    label: str
    model: Any


@dataclass
class ThumbnailTotals:
    generated: int = 0
    skipped: int = 0
    errors: int = 0
    matched_any: bool = False


class Command(BaseCommand):
    """Rebuild thumbnail ImageVariant rows while keeping the legacy command name."""

    help = "Regenerate thumbnail ImageVariant rows for image models with thumbnail specs."
    targets = (
        ThumbnailTarget("AstroImage", AstroImage),
        ThumbnailTarget("ShopProduct", ShopProduct),
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate thumbnails. Kept for compatibility; this command always rebuilds.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report thumbnails that would be regenerated without saving files.",
        )
        parser.add_argument(
            "--object-id",
            type=str,
            help="Regenerate thumbnails only for a single object by primary key.",
        )
        parser.add_argument(
            "--object-ids",
            nargs="+",
            help="Regenerate thumbnails only for the listed objects by primary key.",
        )
        parser.add_argument(
            "-silent",
            "--silent",
            action="store_true",
            help="Report source-file errors but do not fail the command process.",
        )

    def handle(self, *args, **options) -> None:  # noqa: ARG002
        dry_run: bool = options["dry_run"]
        force: bool = options["force"]
        silent: bool = options["silent"]
        target_ids = self._get_target_ids(
            object_id=options.get("object_id"),
            object_ids=options.get("object_ids"),
        )
        totals = ThumbnailTotals()

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made.\n"))
        if force:
            self.stdout.write(self.style.WARNING("FORCE MODE - regenerating thumbnails.\n"))

        for target in self.targets:
            self._regenerate_target(
                target,
                target_ids=target_ids,
                dry_run=dry_run,
                totals=totals,
            )

        self._report_missing_target_ids(target_ids=target_ids, totals=totals)
        self.stdout.write(
            self.style.SUCCESS(
                "\nThumbnail regeneration finished. "
                f"Generated: {totals.generated} | "
                f"Skipped: {totals.skipped} | "
                f"Errors: {totals.errors}"
            )
        )
        if totals.errors and not silent:
            raise CommandError(
                "Thumbnail regeneration failed. "
                f"Resolve {totals.errors} source-file error(s) and rerun the command."
            )

    def _regenerate_target(
        self,
        target: ThumbnailTarget,
        *,
        target_ids: list[str] | None,
        dry_run: bool,
        totals: ThumbnailTotals,
    ) -> None:
        queryset = target.model.objects.all()
        if target_ids is not None:
            try:
                queryset = queryset.filter(pk__in=target_ids)
            except (ValueError, ValidationError):
                queryset = queryset.none()

        count = queryset.count()
        totals.matched_any = totals.matched_any or bool(count)
        self.stdout.write(f"\n{target.label} ({count} records):")

        for obj in queryset.iterator():
            status = self._regenerate_object(obj, dry_run=dry_run)
            if status == "generated":
                totals.generated += 1
            elif status == "skipped":
                totals.skipped += 1
            else:
                totals.errors += 1

    def _regenerate_object(self, obj: Any, *, dry_run: bool) -> str:
        missing_source_path = self._get_missing_source_path(obj)
        if missing_source_path:
            self.stderr.write(
                self.style.ERROR(f"  [ERR ] {obj} - missing source file: {missing_source_path}")
            )
            return "error"

        if not self._get_source_image(obj):
            self.stdout.write(f"  [SKIP] {obj} - no source image")
            return "skipped"

        self.stdout.write(f"  [GEN ] {obj}")
        if dry_run:
            return "generated"

        try:
            if not obj.make_thumbnail():
                return "skipped"
            return "generated"
        except (OSError, ValueError) as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {obj} - source image error: {exc}"))
            return "error"
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {obj} - {exc}"))
            return "error"

    def _get_target_ids(
        self, *, object_id: str | None, object_ids: list[str] | None
    ) -> list[str] | None:
        if object_id and object_ids:
            raise CommandError("Use either --object-id or --object-ids, not both.")
        return [object_id] if object_id else object_ids

    def _report_missing_target_ids(
        self, *, target_ids: list[str] | None, totals: ThumbnailTotals
    ) -> None:
        if target_ids is None or totals.matched_any:
            return

        self.stderr.write(
            self.style.ERROR(
                f"No matching objects found for requested ids: {', '.join(target_ids)}"
            )
        )
        totals.errors += 1

    def _get_source_image(self, obj: Any) -> FieldFile | None:
        if not hasattr(obj, "get_image_variant_sources"):
            return None

        for source in obj.get_image_variant_sources():
            if source.source_image:
                return source.source_image  # type: ignore[no-any-return]

            fallback_source = getattr(obj, source.field_name, None)
            if isinstance(fallback_source, FieldFile):
                return fallback_source
        return None

    def _get_missing_source_path(self, obj: Any) -> str:
        source_image = self._get_source_image(obj)
        if not source_image:
            return ""
        if file_exists_in_storage(source_image):
            return ""
        return str(getattr(source_image, "name", "") or "")
