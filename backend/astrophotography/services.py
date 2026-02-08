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

        return cast(QuerySet[AstroImage], queryset)

    @staticmethod
    def get_travel_highlight_images(slider: MainPageLocation) -> QuerySet[AstroImage]:
        """
        Retrieve images for a specific travel highlight slider.
        Optimized with prefetch_related and select_related.
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
            .filter(place__country=slider.place.country if slider.place else None)
        )
        if slider.place:
            queryset = queryset.filter(place=slider.place)
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
            MainPageLocation.objects.filter(is_active=True)
            .select_related("place", "background_image")
            .prefetch_related(
                "translations",
                "place__translations",
                "background_image__translations",
                "images",
                "images__translations",
            )
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
