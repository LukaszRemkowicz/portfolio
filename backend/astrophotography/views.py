from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from django.shortcuts import get_object_or_404

from core.throttling import GalleryRateThrottle

from .models import MainPageBackgroundImage, MainPageLocation
from .serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    MainPageBackgroundImageSerializer,
    MainPageLocationSerializer,
    TagSerializer,
    TravelHighlightDetailSerializer,
)
from .services import GalleryQueryService


class AstroImageViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving astrophotography images.
    Supports filtering by celestial_object via 'filter' query parameter.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    def get_queryset(self):
        return GalleryQueryService.get_filtered_images(self.request.query_params)

    def get_serializer_class(self):
        if self.action == "list":
            return AstroImageSerializerList
        return AstroImageSerializer


class MainPageBackgroundImageView(ViewSet):
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]
    serializer_class = MainPageBackgroundImageSerializer

    def list(self, request: Request) -> Response:
        instance = MainPageBackgroundImage.objects.order_by("-created_at").first()
        if instance:
            serializer = self.serializer_class(instance, context={"request": request})
            return Response(serializer.data)
        return Response({"url": None})


class MainPageLocationViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing active Main Page Location Sliders.
    """

    queryset = MainPageLocation.objects.filter(is_active=True).order_by("-adventure_date")
    serializer_class = MainPageLocationSerializer
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]


class TravelHighlightsBySlugView(APIView):
    """
    Retrieve travel highlights by country and optional place slug.
    Publicly accessible to support SEO-friendly URLs.
    """

    permission_classes = [AllowAny]  # Allow public access
    serializer_class = TravelHighlightDetailSerializer

    def get(self, request, country_slug=None, place_slug=None):
        # Query the slider by slugs
        # If place_slug is None, we look for a slider with that country slug and no place slug
        # OR we could just find the slider that matches the country slug generally?
        # User requirement: "get object by slug country and slug place"

        filter_kwargs = {"country_slug": country_slug}
        if place_slug:
            filter_kwargs["place_slug"] = place_slug
        else:
            filter_kwargs["place_slug__isnull"] = True

        slider = get_object_or_404(MainPageLocation, is_active=True, **filter_kwargs)
        serializer = self.serializer_class(slider, context={"request": request})
        return Response(serializer.data)


class TagsView(ViewSet):
    """
    ViewSet to return all tags currently associated with AstroImages.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]
    serializer_class = TagSerializer

    def list(self, request: Request) -> Response:
        category_filter = request.query_params.get("filter")
        tags = GalleryQueryService.get_tag_stats(category_filter)
        serializer = self.serializer_class(tags, many=True)

        return Response(serializer.data)
