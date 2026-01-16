# backend/astrophotography/views.py
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
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
            from django_countries import countries

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
