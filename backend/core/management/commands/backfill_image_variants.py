"""Backfill responsive BaseImage variants for existing stored images."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from django.core.management.base import BaseCommand

from astrophotography.models import AstroImage, MainPageBackgroundImage
from programming.models import ProjectImage


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
    help = "Generate missing responsive image variants for BaseImage subclasses."

    targets = (
        VariantBackfillTarget("AstroImage", AstroImage),
        VariantBackfillTarget("MainPageBackgroundImage", MainPageBackgroundImage),
        VariantBackfillTarget("ProjectImage", ProjectImage),
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

    def handle(self, *args, **options) -> None:  # noqa: ARG002
        force: bool = options["force"]
        dry_run: bool = options["dry_run"]
        target_ids = self._get_target_ids(
            object_id=options.get("object_id"),
            object_ids=options.get("object_ids"),
        )

        if target_ids == "invalid":
            return

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

    def _get_target_ids(
        self, *, object_id: str | None, object_ids: list[str] | None
    ) -> list[str] | None | Literal["invalid"]:
        if object_id and object_ids:
            self.stderr.write(self.style.ERROR("Use either --object-id or --object-ids, not both."))
            return "invalid"
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
            queryset = queryset.filter(pk__in=target_ids)

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
                f"No BaseImage objects found for requested ids: {', '.join(target_ids)}"
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

    @staticmethod
    def _get_skip_reason(obj: Any) -> str:
        specs = obj.get_image_variant_specs()
        if not specs:
            return "no variant roles configured"
        if not obj.original_field:
            return "no source image"
        return ""

    def _get_object_sync_status(self, obj: Any) -> SyncStatus:
        try:
            specs = obj.get_image_variant_specs()
            variants_to_generate, variants_to_delete = obj._get_image_variant_sync_plan(specs)
        except FileNotFoundError as exc:
            self._report_missing_source_file(obj, exc)
            return "error"

        if variants_to_generate or variants_to_delete.exists():
            return "needed"
        return "complete"

    def _generate_object_variants(self, obj: Any, *, force: bool) -> BackfillStatus:
        try:
            image_variants = obj.generate_image_variants_or_none(force=force)
            if image_variants is None:
                return "skipped"
            return "generated"
        except FileNotFoundError as exc:
            return self._report_missing_source_file(obj, exc)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {obj} - {exc}"))
            return "error"

    def _report_missing_source_file(self, obj: Any, exc: FileNotFoundError) -> BackfillStatus:
        missing_path = exc.filename or str(exc)
        self.stderr.write(self.style.ERROR(f"  [ERR ] {obj} - missing source file: {missing_path}"))
        return "error"
