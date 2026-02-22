import logging
from typing import Any, List, Optional

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from django.conf import settings
from django.db.models import Model, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from common.decorators.cache import cache_response
from common.throttling import GalleryRateThrottle
from common.utils.logging import sanitize_for_logging
from common.utils.signing import generate_signed_url_params, validate_signed_url

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


@method_decorator(cache_response(timeout=settings.INFINITE_CACHE_TIMEOUT), name="dispatch")
class AstroImageViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving astrophotography images.
    Supports filtering by celestial_object via 'filter' query parameter.

    Note: Caching is safe because URLs are publicly served by Nginx.
    """

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[AstroImage]:
        """Returns the filtered queryset of images."""
        return GalleryQueryService.get_filtered_images(self.request.query_params)

    def get_serializer_class(self) -> type[AstroImageSerializerList] | type[AstroImageSerializer]:
        """Determines which serializer to use based on the action."""
        if self.action in ["list", "latest"]:
            return AstroImageSerializerList
        return AstroImageSerializer

    @method_decorator(cache_response(timeout=settings.INFINITE_CACHE_TIMEOUT))
    @action(detail=False, methods=["get"])
    def latest(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Returns the 9 most recent images for the main page preview."""
        queryset = self.get_queryset().latest()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@method_decorator(cache_response(timeout=settings.INFINITE_CACHE_TIMEOUT), name="dispatch")
class MainPageBackgroundImageView(ViewSet):
    """View to retrieve the most recent background image for the main page."""

    throttle_classes = [GalleryRateThrottle, UserRateThrottle]
    serializer_class = MainPageBackgroundImageSerializer

    def list(self, request: Request) -> Response:
        """Returns the URL of the most recent background image."""
        instance: Optional[MainPageBackgroundImage] = MainPageBackgroundImage.objects.order_by(
            "-created_at"
        ).first()
        if instance:
            serializer: MainPageBackgroundImageSerializer = self.serializer_class(
                instance, context={"request": request}
            )
            return Response(serializer.data)
        return Response({"url": None})


@method_decorator(cache_response(timeout=settings.INFINITE_CACHE_TIMEOUT), name="dispatch")
class MainPageLocationViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for listing active Main Page Location Sliders.

    Note: Caching is safe because URLs are publicly served by Nginx.
    """

    serializer_class = MainPageLocationSerializer
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    def get_queryset(self) -> QuerySet[MainPageLocation]:
        """Returns the optimized queryset for active locations."""
        return GalleryQueryService.get_active_locations()


class TravelHighlightsBySlugView(APIView):
    """
    Retrieve travel highlights by country, place, and date slugs.
    All three segments are required to support SEO-friendly, immutable URLs.
    Publicly accessible.

    URL pattern:
      /travel/{country}/{place}/{date_slug}/
    """

    permission_classes = [AllowAny]
    serializer_class = TravelHighlightDetailSerializer

    def get(
        self,
        request: Request,
        country_slug: Optional[str] = None,
        place_slug: Optional[str] = None,
        date_slug: Optional[str] = None,
    ) -> Response:
        """
        Retrieves highlight details by delegating to the model layer.
        """
        try:
            highlight = (
                MainPageLocation.objects.active()
                .by_slugs(country_slug, place_slug, date_slug)
                .with_images()
                .prefetch_related("translations")
                .get()
            )
        except MainPageLocation.DoesNotExist:
            return Response(
                {"detail": _("No highlight found for these parameters.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer: TravelHighlightDetailSerializer = self.serializer_class(
            highlight, context={"request": request}
        )
        return Response(serializer.data)


@method_decorator(cache_response(timeout=settings.INFINITE_CACHE_TIMEOUT), name="dispatch")
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

        serializer: TagSerializer = self.serializer_class(
            tags, many=True, context={"request": request}
        )
        return Response(serializer.data)


class CelestialObjectCategoriesView(APIView):
    """
    View to return the list of available celestial object categories (choices).
    """

    permission_classes = [AllowAny]
    throttle_classes = [GalleryRateThrottle, UserRateThrottle]

    @method_decorator(cache_response(timeout=settings.INFINITE_CACHE_TIMEOUT))
    def get(self, request: Request) -> Response:
        """Returns the list of available categories."""
        categories: List[str] = [choice[0] for choice in CELESTIAL_OBJECT_CHOICES]
        return Response(categories)


class SecureMediaView(APIView):
    """
    Base view to carefully serve secure, internal media via Nginx X-Accel-Redirect.
    Extending classes MUST implement get_object() and get_file_path().
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_object(self) -> Model:
        raise NotImplementedError("Subclasses must implement get_object")

    def get_file_path(self, obj: Model) -> str:
        raise NotImplementedError("Subclasses must implement get_file_path")

    def get(self, request: Request, slug: str) -> HttpResponse:
        safe_slug: str = sanitize_for_logging(slug)
        signature: Optional[str] = request.query_params.get("s")
        expiration: Optional[str] = request.query_params.get("e")
        safe_signature: str = sanitize_for_logging(signature)
        safe_expiration: str = sanitize_for_logging(expiration)

        if not signature or not expiration:
            logger.warning(
                f"Missing signature params for secure media. Slug: {safe_slug}, "
                f"S: {bool(signature)}, E: {bool(expiration)}"
            )
            return HttpResponse("Missing signature", status=status.HTTP_403_FORBIDDEN)

        if not validate_signed_url(slug, signature, expiration):
            logger.warning(
                f"Invalid or expired signature for secure media. Slug: {safe_slug}, "
                f"S: {safe_signature[:8]}..., E: {safe_expiration}"
            )
            return HttpResponse("Invalid or expired signature", status=status.HTTP_403_FORBIDDEN)

        # Get the object exactly how the subclass wants
        obj: Model = self.get_object()
        file_path: str = self.get_file_path(obj)

        if not file_path:
            logger.error(f"Object record found but file path missing/empty for slug: {safe_slug}")
            raise Http404("Image file not found or is empty")

        response = HttpResponse()
        # This path must match the 'location /protected_media/' block in nginx.conf
        redirect_uri: str = f"/protected_media/{file_path}"
        response["X-Accel-Redirect"] = redirect_uri
        response["Content-Type"] = ""  # Let Nginx determine the content type
        logger.info(f"Serving secure media via Nginx redirect: {redirect_uri}")
        return response


class AstroImageSecureView(SecureMediaView):
    def get_object(self) -> AstroImage:
        slug: str = str(self.kwargs.get("slug"))
        return get_object_or_404(AstroImage, slug=slug)

    def get_file_path(self, obj: Model) -> str:
        assert isinstance(obj, AstroImage)
        return str(obj.path.name)


class ImageURLViewSet(ViewSet):
    """
    Lightweight viewset that ONLY generates signed URLs for images.
    No caching - always returns fresh signatures.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = AstroImage.objects.all().only("slug", "pk")

    def list(self, request: Request) -> Response:
        """
        Returns {slug: signed_url} mapping for requested images.
        Supports query param 'ids' (comma-separated list of PKs).
        """
        queryset: QuerySet[AstroImage] = self.queryset.all()

        # Filter by IDs if provided
        ids_param: Optional[str] = request.query_params.get("ids")
        if ids_param:
            # Split comma-separated UUIDs
            ids: List[str] = [x.strip() for x in ids_param.split(",") if x.strip()]
            if ids:
                queryset = queryset.filter(pk__in=ids)

        url_mapping: dict[str, str] = {}

        for image in queryset:
            url_path: str = reverse("astroimages:secure-image-serve", kwargs={"slug": image.slug})
            params: dict[str, Any] = generate_signed_url_params(
                image.slug, expiration_seconds=settings.SECURE_MEDIA_URL_EXPIRATION
            )
            # Use PK as key to avoid language/translation mismatches
            url_mapping[str(image.pk)] = (
                f"{request.build_absolute_uri(url_path)}?s={params['s']}&e={params['e']}"
            )

        return Response(url_mapping)

    def retrieve(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Returns signed URL for a single image.
        """
        slug: Optional[str] = pk
        image: AstroImage = get_object_or_404(AstroImage, slug=slug)
        url_path: str = reverse("astroimages:secure-image-serve", kwargs={"slug": image.slug})
        params: dict[str, Any] = generate_signed_url_params(
            image.slug, expiration_seconds=settings.SECURE_MEDIA_URL_EXPIRATION
        )
        signed_url: str = f"{request.build_absolute_uri(url_path)}?s={params['s']}&e={params['e']}"

        return Response({"url": signed_url})
