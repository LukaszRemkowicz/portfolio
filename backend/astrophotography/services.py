# backend/astrophotography/services.py
from typing import Any, Dict, Optional

from django_countries import countries

from django.db.models import Q, QuerySet

from .models import AstroImage


class GalleryQueryService:
    """
    Service for handling complex filtering logic for the Astro Gallery.
    Encapsulates QuerySet construction to adhere to SRP.
    """

    @staticmethod
    def get_filtered_images(params: Dict[str, Any]) -> QuerySet[AstroImage]:
        """
        Apply filters to the AstroImage queryset based on provided parameters.
        """
        queryset = AstroImage.objects.all().order_by("-created_at")

        # 1. Filter by Celestial Object (Category)
        category = params.get("filter")
        if category:
            queryset = queryset.filter(celestial_object=category)

        # 2. Filter by Tags
        tag_slug = params.get("tag")
        if tag_slug:
            queryset = queryset.filter(tags__slug__in=[tag_slug])

        # 3. Filter by Travel (Fuzzy country/place match)
        travel = params.get("travel")
        if travel:
            queryset = GalleryQueryService._apply_travel_filter(queryset, travel)

        # 4. Filter by Country and Place (Explicit)
        country = params.get("country")
        place = params.get("place")
        if country:
            queryset = queryset.filter(location=country)
            if place:
                queryset = queryset.filter(Q(place__name__iexact=place) | Q(place__isnull=True))

        return queryset

    @staticmethod
    def get_travel_highlight_images(slider: Any) -> QuerySet[AstroImage]:
        """
        Retrieve images for a specific travel highlight slider.
        """
        queryset = AstroImage.objects.filter(location=slider.country)
        if slider.place:
            queryset = queryset.filter(place=slider.place)
        return queryset.order_by("-created_at")

    @staticmethod
    def get_tag_stats(category_filter: Optional[str] = None) -> QuerySet:
        """
        Aggregate tag counts, optionally filtered by gallery category.
        """
        from taggit.models import Tag

        from django.db.models import Count, Q

        annotation_filter = Q(astroimage__isnull=False)
        if category_filter:
            annotation_filter &= Q(astroimage__celestial_object=category_filter)

        return (
            Tag.objects.filter(astroimage__isnull=False)
            .annotate(num_times=Count("astroimage", filter=annotation_filter, distinct=True))
            .filter(num_times__gt=0)
            .order_by("name")
            .distinct()
        )

    @staticmethod
    def _apply_travel_filter(
        queryset: QuerySet[AstroImage], search_term: str
    ) -> QuerySet[AstroImage]:
        """Internal helper for fuzzy travel filtering"""
        search_term_lower = search_term.lower()
        found_code: Optional[str] = None
        # Fuzzy country match
        for code, name in dict(countries).items():
            if search_term_lower == code.lower() or search_term_lower in name.lower():
                found_code = code
                break
        filter_q = Q(place__name__icontains=search_term)
        if found_code:
            filter_q |= Q(location=found_code)
        # Fallback for manual code entry
        if not found_code:
            filter_q |= Q(location__icontains=search_term)
        return queryset.filter(filter_q)
