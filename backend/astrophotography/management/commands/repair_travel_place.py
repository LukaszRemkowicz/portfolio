"""Restore a known destination country and refresh trip URLs without losing old links."""

from django_countries import countries

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from astrophotography.models import MainPageLocation, Place


class Command(BaseCommand):
    help = "Preview a destination country repair; use --apply to save it and retain old trip URLs."

    def add_arguments(self, parser):
        parser.add_argument("--place-id", type=int, required=True)
        parser.add_argument("--country", required=True, choices=[code for code, _ in countries])
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--if-country-empty", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            place = Place.objects.select_for_update().get(pk=options["place_id"])
        except Place.DoesNotExist as exc:
            if options["if_country_empty"]:
                self.stdout.write("SKIP: Place does not exist; no changes made.")
                return
            raise CommandError("Place does not exist.") from exc
        if options["if_country_empty"] and place.country:
            self.stdout.write(
                f"SKIP: Place {place.pk} already has country {place.country}; no changes made."
            )
            return
        highlights = list(MainPageLocation.objects.select_for_update().filter(place=place))
        mode = "APPLY" if options["apply"] else "DRY RUN"
        self.stdout.write(
            f"{mode}: Place {place.pk} ({place}): {place.country or '(empty)'} -> "
            f"{options['country']}; {len(highlights)} travel highlight(s)."
        )
        if not options["apply"]:
            return
        place.country = options["country"]
        place.save(update_fields=["country"])
        self.stdout.write(
            self.style.SUCCESS("Country restored; previous trip URLs remain supported.")
        )
