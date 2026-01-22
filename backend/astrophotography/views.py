from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from core.throttling import GalleryRateThrottle

from .models import MainPageBackgroundImage, MainPageLocation
from .serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    MainPageBackgroundImageSerializer,
    MainPageLocationSerializer,
)


class AstroImageViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving astrophotography images.
    Supports filtering by celestial_object via 'filter' query parameter.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    def get_queryset(self):
        from .services import GalleryQueryService

        return GalleryQueryService.get_filtered_images(self.request.query_params)

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

    def get(self, request, country_slug=None, place_slug=None):
        from django.shortcuts import get_object_or_404

        from .models import MainPageLocation

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

        # Use Service to get images based on slider's location info
        from .services import GalleryQueryService

        queryset = GalleryQueryService.get_travel_highlight_images(slider)

        # Serialize the results
        serializer = AstroImageSerializerList(queryset, many=True, context={"request": request})

        # We need to return info similar to before so frontend works
        return Response(
            {
                "country": slider.country.name,
                "country_code": slider.country.code,
                "place": slider.place.name if slider.place else None,
                "images": serializer.data,
                "country_slug": slider.country_slug,
                "place_slug": slider.place_slug,
                "story": slider.story,
                "highlight_name": slider.highlight_name,
                "background_image": (
                    slider.background_image.path.url if slider.background_image else None
                ),
                "background_image_thumbnail": (
                    slider.background_image.thumbnail.url
                    if slider.background_image and slider.background_image.thumbnail
                    else None
                ),
                "adventure_date": (MainPageLocationSerializer(slider).data.get("adventure_date")),
                "created_at": slider.created_at,
            }
        )


class TagsView(ViewSet):
    """
    ViewSet to return all tags currently associated with AstroImages.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    def list(self, request: Request) -> Response:
        from .services import GalleryQueryService

        category_filter = request.query_params.get("filter")
        tags = GalleryQueryService.get_tag_stats(category_filter)

        return Response(
            [{"name": tag.name, "slug": tag.slug, "count": tag.num_times} for tag in tags]
        )
