import logging
from typing import Any, Dict, List, Optional

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from common.constants import INFINITE_CACHE_TIMEOUT
from common.decorators.cache import cache_response
from common.throttling import GalleryRateThrottle
from common.utils.logging import sanitize_for_logging
from common.utils.signing import validate_signed_url

from .constants import CELESTIAL_OBJECT_CHOICES
from .models import AstroImage, MainPageBackgroundImage, MainPageLocation, Tag
from .serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    MainPageBackgroundImageSerializer,
    MainPageLocationSerializer,
    TagSerializer,
    TravelHighlightDetailSerializer,
)
from .services import GalleryQueryService

logger: logging.Logger = logging.getLogger(__name__)


@method_decorator(cache_response(timeout=INFINITE_CACHE_TIMEOUT), name="dispatch")
class AstroImageViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving astrophotography images.
    Supports filtering by celestial_object via 'filter' query parameter.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[AstroImage]:
        """Returns the filtered queryset of images."""
        return GalleryQueryService.get_filtered_images(self.request.query_params)

    def get_serializer_class(self):
        """Determines which serializer to use based on the action."""
        if self.action == "list":
            return AstroImageSerializerList
        return AstroImageSerializer


@method_decorator(cache_response(timeout=INFINITE_CACHE_TIMEOUT), name="dispatch")
class MainPageBackgroundImageView(ViewSet):
    """View to retrieve the most recent background image for the main page."""

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]
    serializer_class = MainPageBackgroundImageSerializer

    def list(self, request: Request) -> Response:
        """Returns the URL of the most recent background image."""
        instance = MainPageBackgroundImage.objects.order_by("-created_at").first()
        if instance:
            serializer = self.serializer_class(instance, context={"request": request})
            return Response(serializer.data)
        return Response({"url": None})


@method_decorator(cache_response(timeout=INFINITE_CACHE_TIMEOUT), name="dispatch")
class MainPageLocationViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing active Main Page Location Sliders.
    """

    serializer_class = MainPageLocationSerializer
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    def get_queryset(self) -> QuerySet[MainPageLocation]:
        """Returns the optimized queryset for active locations."""
        return GalleryQueryService.get_active_locations()


class TravelHighlightsBySlugView(APIView):
    """
    Retrieve travel highlights by country and optional place slug.
    Publicly accessible to support SEO-friendly URLs.
    """

    permission_classes = [AllowAny]  # Allow public access
    serializer_class = TravelHighlightDetailSerializer

    @method_decorator(cache_response(timeout=INFINITE_CACHE_TIMEOUT))
    def get(
        self,
        request: Request,
        country_slug: Optional[str] = None,
        place_slug: Optional[str] = None,
    ) -> Response:
        """Retrieves a slider by country and optional place slugs."""
        # Query the slider by slugs
        filter_kwargs: Dict[str, Any] = {"country_slug": country_slug}
        if place_slug:
            filter_kwargs["place_slug"] = place_slug
        else:
            filter_kwargs["place_slug__isnull"] = True
        try:
            slider = MainPageLocation.objects.get(is_active=True, **filter_kwargs)
        except MainPageLocation.DoesNotExist:
            # Fallback: if only country_slug was provided, try matching it against place_slug
            if not place_slug:
                try:
                    slider = MainPageLocation.objects.get(is_active=True, place_slug=country_slug)
                except MainPageLocation.DoesNotExist:
                    safe_slug: str = sanitize_for_logging(country_slug)
                    logger.warning(f"Travel highlight transition failed for slug: {safe_slug}")
                    raise Http404("No MainPageLocation matches the given query.")
            else:
                safe_country: str = sanitize_for_logging(country_slug)
                safe_place: str = sanitize_for_logging(place_slug)
                logger.warning(f"Travel highlight not found: {safe_country}/{safe_place}")
                raise Http404("No MainPageLocation matches the given query.")
        serializer = self.serializer_class(slider, context={"request": request})
        return Response(serializer.data)


@method_decorator(cache_response(timeout=INFINITE_CACHE_TIMEOUT), name="dispatch")
class TagsView(ViewSet):
    """
    ViewSet to return all tags currently associated with AstroImages.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]
    serializer_class = TagSerializer

    def list(self, request: Request) -> Response:
        """Returns tag statistics, optionally filtered by category."""
        category_filter: Optional[str] = request.query_params.get("filter")
        lang: Optional[str] = request.query_params.get("lang")
        tags: QuerySet[Tag] = GalleryQueryService.get_tag_stats(category_filter, language_code=lang)

        serializer = self.serializer_class(tags, many=True, context={"request": request})
        return Response(serializer.data)


class CelestialObjectCategoriesView(APIView):
    """
    View to return the list of available celestial object categories (choices).
    """

    permission_classes = [AllowAny]
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    @method_decorator(cache_response(timeout=INFINITE_CACHE_TIMEOUT))
    def get(self, request: Request) -> Response:
        """Returns the list of available categories."""
        categories: List[str] = [choice[0] for choice in CELESTIAL_OBJECT_CHOICES]
        return Response(categories)


class SecureMediaView(APIView):
    """
    Serves high-resolution images via Nginx X-Accel-Redirect.
    This effectively hides the physical file path from the public.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # Explicitly disable auth to avoid defaults causing redirects

    def get(self, request: Request, slug: str) -> HttpResponse:
        """Validates the signature and redirects to the protected media path."""
        # Sanitize slug for logging
        safe_slug: str = sanitize_for_logging(slug)

        # Validate signature
        signature: Optional[str] = request.query_params.get("s")
        expiration: Optional[str] = request.query_params.get("e")
        if not signature or not expiration:
            logger.warning(f"Missing signature for secure media request: {safe_slug}")
            return HttpResponse("Missing signature", status=403)
        if not validate_signed_url(slug, signature, expiration):
            logger.warning(f"Invalid or expired signature for secure media: {safe_slug}")
            return HttpResponse("Invalid or expired signature", status=403)
        image = get_object_or_404(AstroImage, slug=slug)
        # Security check: Ensure the image actually has a file
        if not image.path:
            logger.error(f"Image record found but file missing for slug: {safe_slug}")
            raise Http404("Image file not found")
        # Construct the protected path for Nginx
        # Note: image.path.name usually looks like 'images/my_photo.jpg'
        # We redirect to /protected_media/images/my_photo.jpg
        # which maps to /app/media/images/my_photo.jpg inside the container
        # The semicolon separates the header from the value in Nginx, but strictly
        # speaking for the header value, we just need the path.
        file_path: str = image.path.name
        response = HttpResponse()
        # This path must match the 'location /protected_media/' block in nginx.conf
        redirect_uri: str = f"/protected_media/{file_path}"
        response["X-Accel-Redirect"] = redirect_uri
        response["Content-Type"] = ""  # Let Nginx determine the content type
        logger.info(f"Serving secure media via Nginx redirect: {redirect_uri}")
        return response
