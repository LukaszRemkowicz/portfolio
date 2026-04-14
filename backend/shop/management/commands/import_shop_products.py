import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from shop.models import ShopProduct


class Command(BaseCommand):
    help = "Import shop products from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the JSON file")
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            help="Delete all existing shop products before import",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing products instead of skipping them",
        )

    def handle(self, *args, **options):
        json_file_path = options["json_file"]

        if not os.path.exists(json_file_path):
            raise CommandError(f'File "{json_file_path}" does not exist')

        try:
            with open(json_file_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CommandError(f"Error reading JSON file: {e}") from e

        if not isinstance(data, list):
            raise CommandError("JSON file must contain a list of objects")

        if options.get("delete_existing"):
            self.stdout.write(self.style.WARNING("Deleting all existing shop products..."))
            ShopProduct.objects.all().delete()

        do_update = options.get("update", False)
        created_count, updated_count, skipped_count = self._import_products(data, do_update)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finished. Created: {created_count}, "
                f"Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )

    def _import_products(self, data, do_update: bool):
        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for index, item in enumerate(data):
                title = item.get("title")
                description = item.get("description", "")
                thumbnail_url = item.get("thumbnail_url", "")
                external_url = item.get("url", "")

                if not title:
                    self.stdout.write(
                        self.style.ERROR(f'Item at index {index} is missing "title". Skipping.')
                    )
                    skipped_count += 1
                    continue

                existing_qs = ShopProduct.objects.filter(translations__title=title)

                if existing_qs.exists():
                    if not do_update:
                        self.stdout.write(
                            self.style.NOTICE(f'Product "{title}" already exists. Skipping.')
                        )
                        skipped_count += 1
                        continue

                    # --update: refresh metadata fields, keep local images untouched
                    product = existing_qs.first()
                    self._apply_fields(product, description, thumbnail_url, external_url)
                    product.save(update_fields=["thumbnail_url", "external_url", "is_active"])

                    # Update translations separately
                    product.set_current_language("en")
                    product.description = description
                    product.save_translations()

                    self.stdout.write(self.style.SUCCESS(f'Updated product: "{title}"'))
                    updated_count += 1
                    continue

                # Create new product — no image download, just save the CDN URL
                product = ShopProduct(external_url=external_url, is_active=True)
                self._apply_fields(product, description, thumbnail_url, external_url)

                product.set_current_language("en")
                product.title = title
                product.description = description

                product.save()
                self.stdout.write(self.style.SUCCESS(f'Created product: "{title}"'))
                created_count += 1

        return created_count, updated_count, skipped_count

    @staticmethod
    def _apply_fields(
        product: ShopProduct, description: str, thumbnail_url: str, external_url: str
    ) -> None:
        """Apply common scalar fields to a product instance (no image downloading)."""
        product.thumbnail_url = thumbnail_url
        product.external_url = external_url
        product.is_active = True
