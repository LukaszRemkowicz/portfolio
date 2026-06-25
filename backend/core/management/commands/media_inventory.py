import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone


class Command(BaseCommand):
    help = "Inspect DB image/file references and media files on disk."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emit the report as one JSON document.",
        )

    def handle(self, *args, **options):
        report = self._build_report()
        if options["json"]:
            self.stdout.write(json.dumps(report, separators=(",", ":")))
            return

        self.stdout.write(
            json.dumps(
                report,
                indent=2,
            )
        )

    def _build_report(self) -> dict[str, object]:
        media_root = Path(str(settings.MEDIA_ROOT))
        discovered_fields: list[dict[str, object]] = []
        references: list[dict[str, object]] = []
        field_reference_counts: Counter[tuple[str, str]] = Counter()
        referenced_file_names: list[str] = []
        warnings: list[str] = []

        for model in sorted(apps.get_models(), key=lambda item: item._meta.label):
            if model._meta.proxy:
                continue

            file_fields = [
                field for field in model._meta.fields if isinstance(field, models.FileField)
            ]
            for field in file_fields:
                discovered_fields.append(
                    {
                        "model": model._meta.label,
                        "field": field.name,
                        "field_type": field.__class__.__name__,
                    }
                )
                manager = model._default_manager.exclude(**{f"{field.name}__isnull": True}).exclude(
                    **{field.name: ""}
                )
                for object_id, file_name in manager.values_list("pk", field.name).iterator():
                    normalized_file_name = str(file_name)
                    if not normalized_file_name:
                        continue
                    referenced_file_names.append(normalized_file_name)
                    field_reference_counts[(model._meta.label, field.name)] += 1
                    references.append(
                        {
                            "model": model._meta.label,
                            "object_id": str(object_id),
                            "field": field.name,
                            "file": normalized_file_name,
                            "exists_on_disk": (media_root / normalized_file_name).is_file(),
                        }
                    )

        disk_files: list[dict[str, object]] = []
        if media_root.is_dir():
            for path in sorted(path for path in media_root.rglob("*") if path.is_file()):
                stat_result = path.stat()
                disk_files.append(
                    {
                        "path": path.relative_to(media_root).as_posix(),
                        "size": stat_result.st_size,
                        "modified_at": datetime.fromtimestamp(
                            stat_result.st_mtime,
                            tz=UTC,
                        ).isoformat(),
                    }
                )
        else:
            warnings.append("MEDIA_ROOT does not exist on disk.")

        referenced_file_set = set(referenced_file_names)
        missing_references = [
            reference for reference in references if not reference["exists_on_disk"]
        ]
        unreferenced_files = [
            disk_file for disk_file in disk_files if disk_file["path"] not in referenced_file_set
        ]

        return {
            "schema_version": 1,
            "generated_at": timezone.now().isoformat(),
            "storage": {
                "media_root": str(media_root),
                "exists": media_root.exists(),
                "is_dir": media_root.is_dir(),
            },
            "summary": {
                "discovered_fields": len(discovered_fields),
                "db_references": len(references),
                "referenced_files": len(referenced_file_set),
                "disk_files": len(disk_files),
                "missing_references": len(missing_references),
                "unreferenced_files": len(unreferenced_files),
            },
            "fields": discovered_fields,
            "field_reference_counts": [
                {
                    "model": model_label,
                    "field": field_name,
                    "references": count,
                }
                for (model_label, field_name), count in sorted(field_reference_counts.items())
            ],
            "references": references,
            "missing_references": missing_references,
            "disk_files": disk_files,
            "unreferenced_files": unreferenced_files,
            "delete_candidates": unreferenced_files,
            "warnings": warnings,
        }
