# backend/astrophotography/services.py
from functools import lru_cache
from typing import Any, Dict, Optional, cast

from django_countries import countries

from django.db.models import Count, Q, QuerySet

from .models import AstroImage, MainPageLocation, Tag


class GalleryQueryService:
    """
    Service for handling complex filtering logic for the Astro Gallery.
    Encapsulates QuerySet construction to adhere to SRP.
    """

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_country_maps() -> Dict[str, Dict[str, str]]:
        """Returns cached country and code maps."""
        return {
            "country_map": {name.lower(): code for code, name in dict(countries).items()},
            "code_map": {code.lower(): code for code in dict(countries).keys()},
        }

    @staticmethod
    def get_filtered_images(params: Dict[str, Any]) -> QuerySet[AstroImage]:
        """
        Apply filters to the AstroImage queryset based on provided parameters.
        Optimized with prefetch_related and select_related to avoid N+1 queries.
        """
        queryset = (
            AstroImage.objects.select_related("place")
            .prefetch_related(
                "translations",
                "place__translations",
                "tags",
                "tags__translations",
                "camera",
                "lens",
                "telescope",
                "tracker",
                "tripod",
            )
            .all()
            .order_by("-created_at")
        )

        # 1. Filter by Celestial Object (Category)
        category = params.get("filter")
        if category:
            queryset = queryset.filter(celestial_object=category)

        # 2. Filter by Tags
        tag_slug = params.get("tag")
        if tag_slug:
            # Note: filtering by translations slug is fine, but prefetching helps representation
            queryset = queryset.filter(tags__translations__slug__in=[tag_slug])

        # 3. Filter by Travel (Fuzzy country/place match)
        travel = params.get("travel")
        if travel:
            queryset = GalleryQueryService._apply_travel_filter(queryset, travel)

        # 4. Filter by Country and Place (Explicit)
        country = params.get("country")
        place = params.get("place")
        if country:
            queryset = queryset.filter(place__country=country)
            if place:
                queryset = queryset.filter(
                    Q(place__translations__name__iexact=place) | Q(place__isnull=True)
                )

        return cast(QuerySet[AstroImage], queryset.order_by("-capture_date"))

    @staticmethod
    def get_travel_highlight_images(slider: MainPageLocation) -> QuerySet[AstroImage]:
        """
        Retrieve images for a specific travel highlight slider.
        Optimized with prefetch_related and select_related.
        """
        queryset = AstroImage.objects.select_related("place").prefetch_related(
            "translations",
            "place__translations",
            "tags",
            "tags__translations",
            "camera",
            "lens",
            "telescope",
            "tracker",
            "tripod",
        )

        # If the user explicitly assigned images in the admin, we want to include them
        explicit_image_ids = list(slider.images.values_list("id", flat=True))

        # If the highlight has a specific place, filter by that place
        # (or its sub-places if it's a region)
        if slider.place:
            if slider.place.is_region:
                sub_place_ids = list(slider.place.sub_places.values_list("id", flat=True))
                # For regions, we also require the date range to match so we don't pull
                # images from an Iceland trip in 2022 when querying for an Iceland trip in 2025.
                if slider.adventure_date:
                    queryset = queryset.filter(
                        Q(
                            place_id__in=sub_place_ids,
                            capture_date__range=(
                                slider.adventure_date.lower,
                                slider.adventure_date.upper,
                            ),
                        )
                        | Q(id__in=explicit_image_ids)
                    )
                else:
                    queryset = queryset.filter(
                        Q(place_id__in=sub_place_ids) | Q(id__in=explicit_image_ids)
                    )
            else:
                queryset = queryset.filter(Q(place=slider.place) | Q(id__in=explicit_image_ids))
        # If it's a country-wide tour (place is null), filter by the slider's country_slug
        else:
            # We must map the slider's country_slug string back to a 2-letter iso code
            # using the GalleryQueryService maps to compare against AstroImage.place.country
            maps = GalleryQueryService._get_country_maps()
            code_map = maps["code_map"]
            country_map = maps["country_map"]

            # Find the 2 letter ISO code based on the slug
            iso_code = code_map.get(slider.country_slug) or country_map.get(slider.country_slug)

            if iso_code:
                queryset = queryset.filter(
                    Q(place__country=iso_code) | Q(id__in=explicit_image_ids)
                )
            else:
                # Fallback if slug formatting is weird
                queryset = queryset.filter(
                    Q(place__country__icontains=slider.country_slug) | Q(id__in=explicit_image_ids)
                )

            # A country tour should show all images taken in that country, even if the
            # individual image has a more specific place assigned to it.

            # We also need to restrict by the slider's date range to only show images
            # taken during this specific adventure.
            if slider.adventure_date:
                queryset = queryset.filter(
                    Q(
                        capture_date__range=(
                            slider.adventure_date.lower,
                            slider.adventure_date.upper,
                        )
                    )
                    | Q(id__in=explicit_image_ids)
                )

        return cast(QuerySet[AstroImage], queryset.order_by("-created_at"))

    @staticmethod
    def get_tag_stats(
        category_filter: Optional[str] = None, language_code: Optional[str] = None
    ) -> QuerySet[Tag]:
        """
        Aggregate tag counts, optionally filtered by gallery category.
        Returns unique tag instances that have at least one associated image.
        """
        annotation_filter = Q(images__isnull=False)
        if category_filter:
            annotation_filter &= Q(images__celestial_object=category_filter)

        return cast(
            QuerySet[Tag],
            Tag.objects.prefetch_related("translations")
            .filter(images__isnull=False)
            .annotate(num_times=Count("images", filter=annotation_filter, distinct=True))
            .filter(num_times__gt=0)
            .order_by("-num_times", "id")
            .distinct(),
        )

    @staticmethod
    def get_active_locations() -> QuerySet[MainPageLocation]:
        """
        Retrieve active MainPageLocation instances with optimized prefetching.
        Prevents N+1 queries for associated place, background image, and slider images.
        """
        return (  # type: ignore[no-any-return]
            MainPageLocation.objects.active()
            .with_place()
            .select_related("background_image")
            .prefetch_related(
                "translations",
                "place__translations",
                "background_image__translations",
            )
            .with_images()
            .prefetch_related("images__translations")
            .order_by("-adventure_date")
        )

    @classmethod
    def _apply_travel_filter(
        cls, queryset: QuerySet[AstroImage], search_term: str
    ) -> QuerySet[AstroImage]:
        """
        Applies a smart fuzzy filter to images based on location and place.
        Optimized with cached dictionary lookup for country mapping.
        """
        search_term_lower = search_term.lower()
        maps = cls._get_country_maps()
        country_map = maps["country_map"]
        code_map = maps["code_map"]

        found_code = code_map.get(search_term_lower) or country_map.get(search_term_lower)

        # Partial name match fallback (if exact match fails)
        if not found_code:
            for name_lower, code in country_map.items():
                if search_term_lower in name_lower:
                    found_code = code
                    break

        filter_q = Q(place__translations__name__icontains=search_term)
        if found_code:
            filter_q |= Q(place__country=found_code)

        # Fallback for manual code entry that might not be in official list
        if not found_code:
            filter_q |= Q(place__country__icontains=search_term)

        return queryset.filter(filter_q)
