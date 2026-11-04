from datetime import date
from io import StringIO

import pytest
from psycopg2.extras import DateRange
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from django.core.management import call_command
from django.urls import reverse
from django.utils import translation

from astrophotography.admin import MainPageLocationForm
from astrophotography.forms import PlaceAdminForm
from astrophotography.models import AstroImage, MainPageLocation, Place
from astrophotography.serializers import MainPageLocationSerializer
from astrophotography.tests.factories import (
    AstroImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
)

pytestmark = pytest.mark.django_db


def test_country_type_is_explicit_in_place_admin(admin_client):
    response = admin_client.get(reverse("admin:astrophotography_place_add"))
    assert "location_type" in response.context["adminform"].form.fields
    response = admin_client.post(
        reverse("admin:astrophotography_place_add"),
        {"location_type": "country", "country": "ES", "name": "Spain", "_save": "Save"},
    )
    assert response.status_code == 302
    country = Place.objects.get(country="ES")
    assert country.name == ""
    assert not country.is_region


def test_region_type_keeps_country_and_sub_places(admin_client):
    wetlina = PlaceFactory(name="Wetlina", country="PL")
    response = admin_client.post(
        reverse("admin:astrophotography_place_add"),
        {
            "location_type": "region",
            "name": "Bieszczady",
            "country": "PL",
            "sub_places": [wetlina.pk],
            "_save": "Save",
        },
    )
    assert response.status_code == 302
    region = Place.objects.translated("en", name="Bieszczady").get()
    assert region.is_region
    assert region.country == "PL"
    assert list(region.sub_places.all()) == [wetlina]


def test_named_destination_requires_name():
    form = PlaceAdminForm(data={"location_type": "place", "country": "ES", "name": ""})
    assert not form.is_valid()
    assert "name" in form.errors


def test_region_scope_uses_country_children_without_expanding_named_stops():
    country = PlaceFactory(name="", country="ES")
    stop = PlaceFactory(name="Wetlina", country="PL")
    region = PlaceFactory(name="Our route", is_region=True, country="")
    region.sub_places.set([country, stop])
    included = [
        AstroImageFactory(place=PlaceFactory(country="ES"), capture_date=date(2026, 6, 5)),
        AstroImageFactory(place=stop, capture_date=date(2026, 6, 5)),
    ]
    AstroImageFactory(place=PlaceFactory(country="PL"), capture_date=date(2026, 6, 5))
    end_date_image = AstroImageFactory(place=stop, capture_date=date(2026, 6, 15))
    trip = MainPageLocationFactory(
        place=region, adventure_date=DateRange(date(2026, 6, 1), date(2026, 6, 15))
    )
    assert set(AstroImage.objects.for_travel_highlight(trip)) == set(included)
    assert set(MainPageLocationForm(instance=trip).fields["images"].queryset) == {
        *included,
        end_date_image,
    }


def test_changing_trip_destination_uses_submitted_place(admin_client):
    old_place = PlaceFactory(country="PL")
    country = PlaceFactory(name="", country="ES")
    image = AstroImageFactory(place=PlaceFactory(country="ES"))
    trip = MainPageLocationFactory(place=old_place)
    response = admin_client.post(
        reverse("admin:astrophotography_mainpagelocation_change", args=[trip.pk]),
        {
            "place": country.pk,
            "highlight_name": "Spain",
            "adventure_date_0": "2026-06-01",
            "adventure_date_1": "2026-06-15",
            "images": [image.pk],
            "background_image": image.pk,
            "_save": "Save",
        },
    )
    assert response.status_code == 302
    trip.refresh_from_db()
    assert trip.place == country
    assert list(trip.images.all()) == [image]


def test_country_trip_detail_resolves_fallback_place_segment(api_client):
    trip = MainPageLocationFactory(place=PlaceFactory(name="", country="ES"))
    response = api_client.get(f"/v1/travel/spain/explore/{trip.date_slug}/?lang=en")
    assert response.status_code == 200
    assert response.data["pk"] == trip.pk


def test_region_country_repair_preserves_old_url(api_client):
    region = PlaceFactory(name="Bieszczady", is_region=True, country="")
    trip = MainPageLocationFactory(place=region)
    old_url = f"/v1/travel/explore/bieszczady/{trip.date_slug}/"
    region.country = "PL"
    region.save()
    trip.save()
    trip.refresh_from_db()
    assert trip.country_slug == "poland"
    assert api_client.get(old_url).status_code == 200
    response = api_client.get(f"/v1/travel/poland/bieszczady/{trip.date_slug}/")
    assert response.status_code == 200
    assert response.data["pk"] == trip.pk


def test_trip_slugs_do_not_change_with_admin_language():
    place = PlaceFactory(name="Cabo de Gata", country="ES")
    place.set_current_language("pl")
    place.name = "Przylądek Gata"
    place.save()
    with translation.override("pl"):
        trip = MainPageLocationFactory(place=place)
    assert trip.country_slug == "spain"
    assert trip.place_slug == "cabo-de-gata"


@pytest.mark.parametrize(("lang", "expected_title"), [("en", ""), ("pl", "Polski tytuł")])
def test_travel_title_never_falls_back_from_english_to_polish(lang, expected_title):
    trip = MainPageLocationFactory(highlight_name="Spain trip", highlight_title="", story="")
    trip.set_current_language("pl")
    trip.highlight_name = "Hiszpania"
    trip.highlight_title = "Polski tytuł"
    trip.story = "Polska historia"
    trip.save()
    request = Request(APIRequestFactory().get("/", {"lang": lang}))
    data = MainPageLocationSerializer(trip, context={"request": request}).data
    assert data["highlight_title"] == expected_title
    if lang == "en":
        assert data["story"] == ""
        assert data["story_preview"] == ""


def test_travel_labels_omit_empty_country():
    trip = MainPageLocationFactory(
        place=PlaceFactory(name="Scandinavia", is_region=True, country=""),
        highlight_name="Northern nights",
    )
    assert trip.get_full_location("en") == "Northern nights"


def test_repair_place_country_defaults_to_dry_run_and_preserves_links():
    region = PlaceFactory(name="Bieszczady", is_region=True, country="")
    trip = MainPageLocationFactory(place=region)
    output = StringIO()
    call_command("repair_travel_place", place_id=region.pk, country="PL", stdout=output)
    region.refresh_from_db()
    assert not region.country
    assert "DRY RUN" in output.getvalue()
    call_command("repair_travel_place", place_id=region.pk, country="PL", apply=True)
    region.refresh_from_db()
    trip.refresh_from_db()
    assert region.country == "PL"
    assert trip.country_slug == "poland"
    assert MainPageLocation.objects.by_slugs("explore", "bieszczady", trip.date_slug).get() == trip
    call_command("repair_travel_place", place_id=region.pk, country="PL", apply=True)
    trip.refresh_from_db()
    assert len(trip.legacy_slugs) == 1


def test_repair_place_if_country_empty_skips_missing_place():
    output = StringIO()
    call_command(
        "repair_travel_place",
        place_id=2**31 - 1,
        country="PL",
        apply=True,
        if_country_empty=True,
        stdout=output,
    )
    assert "SKIP" in output.getvalue()


def test_repair_place_if_country_empty_does_not_overwrite_populated_country(monkeypatch):
    place = PlaceFactory(name="Bieszczady", is_region=True, country="ES")
    save = Place.save
    save_calls = []

    def record_save(instance, *args, **kwargs):
        save_calls.append(instance.pk)
        return save(instance, *args, **kwargs)

    monkeypatch.setattr(Place, "save", record_save)
    call_command(
        "repair_travel_place",
        place_id=place.pk,
        country="PL",
        apply=True,
        if_country_empty=True,
        stdout=StringIO(),
    )
    place.refresh_from_db()
    assert place.country == "ES"
    assert save_calls == []


def test_repair_place_if_country_empty_keeps_aliases_unchanged_on_second_run(monkeypatch):
    region = PlaceFactory(name="Bieszczady", is_region=True, country="")
    trip = MainPageLocationFactory(place=region)
    call_command(
        "repair_travel_place",
        place_id=region.pk,
        country="PL",
        apply=True,
        if_country_empty=True,
    )
    region.refresh_from_db()
    trip.refresh_from_db()
    aliases_after_repair = trip.legacy_slugs
    assert region.country == "PL"
    assert aliases_after_repair

    save = Place.save
    save_calls = []

    def record_save(instance, *args, **kwargs):
        save_calls.append(instance.pk)
        return save(instance, *args, **kwargs)

    monkeypatch.setattr(Place, "save", record_save)
    call_command(
        "repair_travel_place",
        place_id=region.pk,
        country="PL",
        apply=True,
        if_country_empty=True,
        stdout=StringIO(),
    )
    trip.refresh_from_db()
    assert save_calls == []
    assert trip.legacy_slugs == aliases_after_repair


def test_place_country_change_refreshes_trip_slugs_and_cached_location(api_client):
    region = PlaceFactory(name="Bieszczady", is_region=True, country="")
    trip = MainPageLocationFactory(place=region)
    url = reverse("astroimages:travel-highlights-list") + "?lang=en"
    assert api_client.get(url).json()[0]["place"]["country"] == ""
    region.country = "PL"
    region.save()
    trip.refresh_from_db()
    assert trip.country_slug == "poland"
    data = api_client.get(url).json()[0]
    assert data["place"]["country"] == "Poland"
    assert data["country_slug"] == "poland"


def test_completed_title_update_refreshes_cached_english_without_changing_polish(api_client):
    trip = MainPageLocationFactory(highlight_title="")
    trip.set_current_language("pl")
    trip.highlight_title = "Polski tytuł"
    trip.save()
    url = reverse("astroimages:travel-highlights-list")
    assert api_client.get(url, {"lang": "en"}).json()[0]["highlight_title"] == ""
    assert api_client.get(url, {"lang": "pl"}).json()[0]["highlight_title"] == "Polski tytuł"
    trip.set_current_language("en")
    trip.highlight_title = "English title"
    trip.save()
    assert api_client.get(url, {"lang": "en"}).json()[0]["highlight_title"] == "English title"
    assert api_client.get(url, {"lang": "pl"}).json()[0]["highlight_title"] == "Polski tytuł"


def test_ambiguous_legacy_url_returns_404(api_client):
    first = MainPageLocationFactory(place=PlaceFactory(name="First", country="PL"))
    second = MainPageLocationFactory(place=PlaceFactory(name="Second", country="ES"))
    MainPageLocation.objects.filter(pk__in=[first.pk, second.pk]).update(
        legacy_slugs=[{"country": "explore", "place": "old-region"}]
    )
    assert api_client.get(f"/v1/travel/explore/old-region/{first.date_slug}/").status_code == 404


def test_nested_regions_and_cycles_do_not_expand_to_unrelated_countries():
    country = PlaceFactory(name="", country="ES")
    parent = PlaceFactory(name="Parent", country="", is_region=True)
    child = PlaceFactory(name="Child", country="", is_region=True)
    parent.sub_places.add(child)
    child.sub_places.add(parent, country)
    included = AstroImageFactory(place=PlaceFactory(country="ES"), capture_date=date(2025, 1, 5))
    AstroImageFactory(place=PlaceFactory(country="PL"), capture_date=date(2025, 1, 5))
    trip = MainPageLocationFactory(place=parent)
    assert list(AstroImage.objects.for_travel_highlight(trip)) == [included]
