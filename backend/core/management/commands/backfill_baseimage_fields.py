"""Backfill Phase 2 BaseImage fields from the legacy field family.

This command copies stored file references only. It does not re-encode images,
dispatch Celery, or touch thumbnail content.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand
from django.db.models import Model

from astrophotography.models import AstroImage, MainPageBackgroundImage
from programming.models import ProjectImage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BackfillTarget:
    label: str
    model: Any


class Command(BaseCommand):
    help = "Backfill BaseImage original/original_webp fields from legacy fields."

    targets = (
        BackfillTarget("AstroImage", AstroImage),
        BackfillTarget("MainPageBackgroundImage", MainPageBackgroundImage),
        BackfillTarget("ProjectImage", ProjectImage),
    )

    def handle(self, *args, **options) -> None:  # noqa: ARG002
        total_updated = 0
        total_skipped = 0
        total_targets = 0

        logger.info("Starting BaseImage field backfill")

        for target in self.targets:
            count, updated, skipped = self._backfill_target(target)
            total_targets += count
            total_updated += updated
            total_skipped += skipped

        self.stdout.write(
            self.style.SUCCESS(
                "BaseImage field backfill finished. "
                f"Rows scanned: {total_targets} | "
                f"Updated: {total_updated} | Skipped: {total_skipped}"
            )
        )
        logger.info(
            "Finished BaseImage field backfill",
            extra={
                "rows_scanned": total_targets,
                "rows_updated": total_updated,
                "rows_skipped": total_skipped,
            },
        )

    def _backfill_target(self, target: BackfillTarget) -> tuple[int, int, int]:
        model = target.model
        queryset = model.objects.all()
        scanned = queryset.count()
        updated = 0
        skipped = 0

        for instance in queryset.iterator():
            updated_fields = self._backfill_instance(instance)
            if updated_fields:
                instance.save(update_fields=updated_fields)
                updated += 1
                logger.info(
                    "Backfilled BaseImage fields for instance",
                    extra={
                        "target": target.label,
                        "instance_id": str(instance.pk),
                        "updated_fields": updated_fields,
                    },
                )
            else:
                skipped += 1
                logger.info(
                    "Skipped BaseImage field backfill for instance because nothing changed",
                    extra={"target": target.label, "instance_id": str(instance.pk)},
                )

        self.stdout.write(
            f"{target.label}: scanned {scanned}, updated {updated}, skipped {skipped}"
        )
        logger.info(
            "Processed BaseImage field backfill target",
            extra={
                "target": target.label,
                "rows_scanned": scanned,
                "rows_updated": updated,
                "rows_skipped": skipped,
            },
        )
        return scanned, updated, skipped

    def _backfill_instance(self, instance: Any) -> list[str]:
        updated_fields: list[str] = []

        current_original_name = self._get_field_name(instance, "original")
        if not current_original_name:
            original_name = self._resolve_original_name(instance)
            if original_name:
                instance.original = original_name
                updated_fields.append("original")

        current_original_webp_name = self._get_field_name(instance, "original_webp")
        if not current_original_webp_name:
            original_webp_name = self._resolve_original_webp_name(instance)
            if original_webp_name:
                instance.original_webp = original_webp_name
                updated_fields.append("original_webp")

        return updated_fields

    def _resolve_original_name(self, instance: Model) -> str:
        original_image_name = self._get_field_name(instance, "original_image")
        if original_image_name:
            return original_image_name
        return self._get_field_name(instance, "path")

    def _resolve_original_webp_name(self, instance: Model) -> str:
        path_name = self._get_field_name(instance, "path")
        if path_name.lower().endswith(".webp"):
            return path_name
        return ""

    def _get_field_name(self, instance: Model, field_name: str) -> str:
        field = getattr(instance, field_name, None)
        return str(getattr(field, "name", "") or "")
