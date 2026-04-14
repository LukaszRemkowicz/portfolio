"""Configure the singleton shop settings record and its default translated copy."""

from django.core.management.base import BaseCommand

from ._seed_shop_settings_defaults import get_or_create_shop_settings, seed_shop_settings_defaults


class Command(BaseCommand):
    """Create or update the singleton shop settings record with default translated copy."""

    help = (
        "Create the ShopSettings singleton when needed and populate default English and "
        "Polish title/description values."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing translated title/description values with the shop defaults.",
        )
        parser.add_argument(
            "--skip-missing",
            action="store_true",
            help=(
                "Exit successfully without creating the ShopSettings singleton "
                "when it does not exist."
            ),
        )

    def handle(self, *args, **options) -> None:
        if options["skip_missing"]:
            from shop.models import ShopSettings

            shop_settings = ShopSettings.get_current()
            if shop_settings is None:
                self.stdout.write("ShopSettings does not exist yet. Skipping.")
                return
            created = False
        else:
            shop_settings, created = get_or_create_shop_settings()

        if created:
            self.stdout.write(self.style.SUCCESS("Created ShopSettings singleton."))

        changed_by_language = seed_shop_settings_defaults(
            shop_settings,
            overwrite=options["overwrite"],
        )

        for language_code, changed in changed_by_language.items():
            status = "seeded" if changed else "kept existing values"
            self.stdout.write(f"{language_code}: {status}")

        self.stdout.write(self.style.SUCCESS("Shop settings defaults processed."))
