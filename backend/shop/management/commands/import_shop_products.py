import json
import os

import requests

from django.core.files.base import ContentFile
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

        created_count, skipped_count = self._import_products(data)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finished. Created: {created_count}, Skipped: {skipped_count}"
            )
        )

    def _import_products(self, data):
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for index, item in enumerate(data):
                title = item.get("title")
                description = item.get("description", "")
                thumbnail_url = item.get("thumbnail_url")
                external_url = item.get("url", "")

                if not title:
                    self.stdout.write(
                        self.style.ERROR(f'Item at index {index} is missing "title". Skipping.')
                    )
                    skipped_count += 1
                    continue

                if ShopProduct.objects.filter(translations__title=title).exists():
                    self.stdout.write(
                        self.style.NOTICE(f'Product "{title}" already exists. Skipping.')
                    )
                    skipped_count += 1
                    continue

                product = ShopProduct(external_url=external_url, is_active=True)

                # set translatable fields
                product.set_current_language("en")
                product.title = title
                product.description = description

                if thumbnail_url:
                    self._download_product_image(product, title, thumbnail_url)

                product.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully created product: {title}"))

        return created_count, skipped_count

    def _download_product_image(self, product, title, thumbnail_url):
        try:
            self.stdout.write(f'Downloading image for "{title}"...')
            response = requests.get(thumbnail_url, timeout=30)
            response.raise_for_status()

            # Use filename from URL or title
            filename = os.path.basename(thumbnail_url.split("?")[0])
            if not filename or "." not in filename:
                filename = f"{title.lower().replace(' ', '_')[:50]}.webp"

            product.path.save(filename, ContentFile(response.content), save=False)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to download image from {thumbnail_url}: {e}")
            )
