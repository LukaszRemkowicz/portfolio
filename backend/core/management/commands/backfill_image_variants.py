"""Backfill responsive image variants for configured variant-producing models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields.files import FieldFile

from astrophotography.models import AstroImage, MainPageBackgroundImage
from common.utils.image import file_exists_in_storage
from programming.models import ProjectImage
from shop.models import ShopProduct, ShopSettings


@dataclass(frozen=True)
class VariantBackfillTarget:
    label: str
    model: Any


@dataclass
class VariantBackfillTotals:
    generated: int = 0
    skipped: int = 0
    errors: int = 0
    matched_any: bool = False


BackfillStatus = Literal["generated", "skipped", "error"]
SyncStatus = Literal["needed", "complete", "error"]


class Command(BaseCommand):
    help = "Generate missing responsive image variants for variant-producing models."

    targets = (
        VariantBackfillTarget("AstroImage", AstroImage),
        VariantBackfillTarget("MainPageBackgroundImage", MainPageBackgroundImage),
        VariantBackfillTarget("ProjectImage", ProjectImage),
        VariantBackfillTarget("ShopProduct", ShopProduct),
        VariantBackfillTarget("ShopSettings", ShopSettings),
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate variants even when variant rows already look complete.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report variant rows that would be generated without saving files.",
        )
        parser.add_argument(
            "--object-id",
            type=str,
            help="Backfill only a single BaseImage object by primary key.",
        )
        parser.add_argument(
            "--object-ids",
            nargs="+",
            help="Backfill only the listed BaseImage objects by primary key.",
        )
        parser.add_argument(
            "-silent",
            "--silent",
            action="store_true",
            help="Report source-file errors but do not fail the command process.",
        )

    def handle(self, *args, **options) -> None:  # noqa: ARG002
        force: bool = options["force"]
        dry_run: bool = options["dry_run"]
        silent: bool = options["silent"]
        target_ids = self._get_target_ids(
            object_id=options.get("object_id"),
            object_ids=options.get("object_ids"),
        )

        self._announce_mode(force=force, dry_run=dry_run)
        totals = VariantBackfillTotals()

        for target in self.targets:
            self._backfill_target(
                target,
                target_ids=target_ids,
                totals=totals,
                force=force,
                dry_run=dry_run,
            )

        self._report_missing_target_ids(target_ids=target_ids, totals=totals)
        self._report_totals(totals)
        if totals.errors and not silent:
            raise CommandError(
                "Image variant backfill failed. "
                f"Resolve {totals.errors} source-file error(s) and rerun the command."
            )

    def _get_target_ids(
        self, *, object_id: str | None, object_ids: list[str] | None
    ) -> list[str] | None:
        if object_id and object_ids:
            raise CommandError("Use either --object-id or --object-ids, not both.")
        return [object_id] if object_id else object_ids

    def _announce_mode(self, *, force: bool, dry_run: bool) -> None:
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made.\n"))
        if force:
            self.stdout.write(self.style.WARNING("FORCE MODE - regenerating variants.\n"))

    def _backfill_target(
        self,
        target: VariantBackfillTarget,
        *,
        target_ids: list[str] | None,
        totals: VariantBackfillTotals,
        force: bool,
        dry_run: bool,
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
            self._count_status(
                totals,
                self._backfill_object(obj, force=force, dry_run=dry_run),
            )

    @staticmethod
    def _count_status(totals: VariantBackfillTotals, status: BackfillStatus) -> None:
        if status == "generated":
            totals.generated += 1
        elif status == "skipped":
            totals.skipped += 1
        else:
            totals.errors += 1

    def _report_missing_target_ids(
        self, *, target_ids: list[str] | None, totals: VariantBackfillTotals
    ) -> None:
        if target_ids is None or totals.matched_any:
            return

        self.stderr.write(
            self.style.ERROR(
                f"No matching objects found for requested ids: {', '.join(target_ids)}"
            )
        )
        totals.errors += 1

    def _report_totals(self, totals: VariantBackfillTotals) -> None:
        self.stdout.write(
            self.style.SUCCESS(
                "\nImage variant backfill finished. "
                f"Generated: {totals.generated} | "
                f"Skipped: {totals.skipped} | "
                f"Errors: {totals.errors}"
            )
        )

    def _backfill_object(self, obj: Any, *, force: bool, dry_run: bool) -> BackfillStatus:
        if not self._has_image_variants_relation(obj):
            self._report_missing_source_path(obj, "missing generic variants relation")
            return "error"

        missing_source_path = self._get_missing_source_path(obj)
        if missing_source_path:
            self._report_missing_source_path(obj, missing_source_path)
            return "error"

        skip_reason = self._get_skip_reason(obj)
        if skip_reason:
            self.stdout.write(f"  [SKIP] {obj} - {skip_reason}")
            return "skipped"

        if not force:
            sync_status = self._get_object_sync_status(obj)
            if sync_status == "error":
                return "error"
            if sync_status == "complete":
                self.stdout.write(f"  [SKIP] {obj} - variants complete")
                return "skipped"

        self.stdout.write(f"  [GEN ] {obj}")
        if dry_run:
            return "generated"

        return self._generate_object_variants(obj, force=force)

    def _get_skip_reason(self, obj: Any) -> str:
        if not self._get_source_image(obj):
            return "no source image"
        return ""

    @staticmethod
    def _has_image_variants_relation(obj: Any) -> bool:
        return hasattr(obj, "variants")

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

    def _get_object_sync_status(self, obj: Any) -> SyncStatus:
        try:
            pending_sync = obj.has_pending_image_variant_sync()
        except FileNotFoundError as exc:
            self._report_missing_source_file(obj, exc)
            return "error"
        except (OSError, ValueError) as exc:
            self._report_source_error(obj, exc)
            return "error"

        if pending_sync:
            return "needed"
        return "complete"

    def _generate_object_variants(self, obj: Any, *, force: bool) -> BackfillStatus:
        try:
            changed_variant_count = obj.sync_image_variants(force=force)
            if changed_variant_count == 0:
                return "skipped"
            return "generated"
        except FileNotFoundError as exc:
            return self._report_missing_source_file(obj, exc)
        except (OSError, ValueError) as exc:
            return self._report_source_error(obj, exc)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {obj} - {exc}"))
            return "error"

    def _report_missing_source_file(self, obj: Any, exc: FileNotFoundError) -> BackfillStatus:
        missing_path = exc.filename or str(exc)
        self._report_missing_source_path(obj, missing_path)
        return "error"

    def _report_source_error(self, obj: Any, exc: Exception) -> BackfillStatus:
        self.stderr.write(self.style.ERROR(f"  [ERR ] {obj} - source image error: {exc}"))
        return "error"

    def _report_missing_source_path(self, obj: Any, missing_path: str) -> None:
        self.stderr.write(self.style.ERROR(f"  [ERR ] {obj} - missing source file: {missing_path}"))
