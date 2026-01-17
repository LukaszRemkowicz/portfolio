# backend/astrophotography/views.py
from django_countries import countries
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from core.throttling import GalleryRateThrottle

from .models import AstroImage, MainPageBackgroundImage, MainPageLocationSlider
from .serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    MainPageBackgroundImageSerializer,
    MainPageLocationSliderSerializer,
)


class AstroImageViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving astrophotography images.
    Supports filtering by celestial_object via 'filter' query parameter.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = AstroImage.objects.all().order_by("-created_at")

        # Filter by Celestial Object
        filter_value = self.request.query_params.get("filter")
        if filter_value:
            queryset = queryset.filter(celestial_object=filter_value)

        # Filter by Tags
        tag_slug = self.request.query_params.get("tag")
        if tag_slug:
            queryset = queryset.filter(tags__name__in=[tag_slug])

        # Filter by Travel (matches location or place name)
        travel_param = self.request.query_params.get("travel")
        if travel_param:

            from django.db.models import Q

            # Implementation of a fuzzy country match
            found_code = None
            search_term = travel_param.lower()
            for code, name in dict(countries).items():
                if search_term == code.lower() or search_term in name.lower():
                    found_code = code
                    break

            filter_q = Q(place__name__icontains=travel_param)
            if found_code:
                filter_q |= Q(location=found_code)

            # Additional check for manual entry if no code found
            if not found_code:
                filter_q |= Q(location__icontains=travel_param)

            queryset = queryset.filter(filter_q)

        # Filter by Country and Place (explicit parameters)
        country_param = self.request.query_params.get("country")
        place_param = self.request.query_params.get("place")

        if country_param:
            from django.db.models import Q

            # Filter by country code
            queryset = queryset.filter(location=country_param)

            # If place is specified, also filter by place
            if place_param:
                queryset = queryset.filter(
                    Q(place__name__iexact=place_param) | Q(place__isnull=True)
                )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AstroImageSerializerList
        return AstroImageSerializer


class MainPageBackgroundImageView(ViewSet):
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    def list(self, request: Request) -> Response:
        instance = MainPageBackgroundImage.objects.order_by("-created_at").first()
        if instance:
            serializer = MainPageBackgroundImageSerializer(instance, context={"request": request})
            return Response(serializer.data)
        return Response({"url": None})


class MainPageLocationSliderViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing active Main Page Location Sliders.
    """

    queryset = MainPageLocationSlider.objects.filter(is_active=True).order_by("country")
    serializer_class = MainPageLocationSliderSerializer
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]


class TravelHighlightsBySlugView(APIView):
    """
    Retrieve travel highlights by country and optional place slug.
    Publicly accessible to support SEO-friendly URLs.
    """

    permission_classes = [AllowAny]  # Allow public access

    def get(self, request, country_slug=None, place_slug=None):
        from django.shortcuts import get_object_or_404

        from .models import MainPageLocationSlider

        # Query the slider by slugs
        # If place_slug is None, we look for a slider with that country slug and no place slug
        # OR we could just find the slider that matches the country slug generally?
        # User requirement: "get object by slug country and slug place"

        filter_kwargs = {"country_slug": country_slug}
        if place_slug:
            filter_kwargs["place_slug"] = place_slug
        else:
            filter_kwargs["place_slug__isnull"] = True

        slider = get_object_or_404(MainPageLocationSlider, is_active=True, **filter_kwargs)

        # now get images based on slider's location info
        # User requirement: filter by location and place from the slider object

        queryset = AstroImage.objects.filter(location=slider.country)

        if slider.place:
            queryset = queryset.filter(place=slider.place)

        queryset = queryset.order_by("-created_at")

        # Serialize the results
        serializer = AstroImageSerializerList(queryset, many=True, context={"request": request})

        # We need to return info similar to before so frontend works
        return Response(
            {
                "country": slider.country.name,
                "country_code": slider.country.code,
                "place": slider.place.name if slider.place else None,
                "images": serializer.data,
                # include slugs in response if helpful, though frontend likely has them from URL
                "country_slug": slider.country_slug,
                "place_slug": slider.place_slug,
            }
        )
