# backend/astrophotography/services.py
from typing import Any, Dict, Optional, cast

from django_countries import countries

from django.db.models import Count, Q, QuerySet

from .models import AstroImage, Tag


class GalleryQueryService:
    """
    Service for handling complex filtering logic for the Astro Gallery.
    Encapsulates QuerySet construction to adhere to SRP.
    """

    @staticmethod
    def get_filtered_images(params: Dict[str, Any]) -> QuerySet[AstroImage]:
        """
        Apply filters to the AstroImage queryset based on provided parameters.
        Optimized with prefetch_related and select_related to avoid N+1 queries.
        """
        queryset = (
            AstroImage.objects.select_related("place")
            .prefetch_related(
                "tags", "camera", "lens", "telescope", "tracker", "tripod"
            )  # type: ignore[misc]
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

        return queryset

    @staticmethod
    def get_travel_highlight_images(slider: Any) -> QuerySet[AstroImage]:
        """
        Retrieve images for a specific travel highlight slider.
        Optimized with prefetch_related and select_related.
        """
        queryset = (
            AstroImage.objects.select_related("place")
            .prefetch_related(
                "tags", "camera", "lens", "telescope", "tracker", "tripod"
            )  # type: ignore[misc]
            .filter(place__country=slider.place.country if slider.place else None)
        )
        if slider.place:
            queryset = queryset.filter(place=slider.place)
        return queryset.order_by("-created_at")

    @staticmethod
    def get_tag_stats(
        category_filter: Optional[str] = None, language_code: Optional[str] = None
    ) -> QuerySet:
        """
        Aggregate tag counts, optionally filtered by gallery category.
        Returns unique tag instances that have at least one associated image.
        """
        annotation_filter = Q(images__isnull=False)
        if category_filter:
            annotation_filter &= Q(images__celestial_object=category_filter)

        return cast(
            QuerySet,
            Tag.objects.filter(images__isnull=False)
            .annotate(num_times=Count("images", filter=annotation_filter, distinct=True))
            .filter(num_times__gt=0)
            .order_by("-num_times", "id")
            .distinct(),
        )

    @staticmethod
    def _apply_travel_filter(
        queryset: QuerySet[AstroImage], search_term: str
    ) -> QuerySet[AstroImage]:
        """
        Applies a smart fuzzy filter to images based on location and place.

        Matches the search term against:
        1. Country Names: Uses a lookup to convert terms like 'Poland' to their ISO code ('PL').
        2. Country Codes: Matches direct Alpha-2 codes (e.g., 'PL').
        3. Place Names: Matches specific cities/regions (e.g., 'Tenerife')
           via case-insensitive lookup.

        This allows the frontend to send a single search string while the backend handles
        mapping it to the appropriate database fields (location code vs. place name).
        """
        search_term_lower = search_term.lower()
        found_code: Optional[str] = None
        # Fuzzy country match
        for code, name in dict(countries).items():
            matches_code = search_term_lower == code.lower()
            matches_name = search_term_lower in name.lower()
            if matches_code or matches_name:
                found_code = code
                break
        filter_q = Q(place__translations__name__icontains=search_term)
        if found_code:
            filter_q |= Q(place__country=found_code)
        # Fallback for manual code entry
        if not found_code:
            filter_q |= Q(place__country__icontains=search_term)
        return queryset.filter(filter_q)
