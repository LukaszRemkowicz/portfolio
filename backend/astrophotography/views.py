import logging
from typing import Any, cast

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
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from common.decorators.cache import cache_response
from common.throttling import GalleryRateThrottle
from common.utils.signing import generate_signed_url_params
from core.views import GenericAdminSecureMediaView, SecureMediaView

from .constants import CELESTIAL_OBJECT_CHOICES
from .models import AstroImage, MainPageBackgroundImage, MainPageLocation, Tag
from .pagination import AstroImagePagination
from .serializers import (
    AstroImageSerializer,
    AstroImageSerializerList,
    MainPageBackgroundImageSerializer,
    MainPageLocationSerializer,
    TagSerializer,
    TravelHighlightDetailSerializer,
)

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
    pagination_class = AstroImagePagination

    def get_queryset(self) -> QuerySet[AstroImage]:
        """Returns the filtered queryset of images."""
        return cast(QuerySet[AstroImage], AstroImage.objects.for_gallery(self.request.query_params))

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
        queryset = MainPageBackgroundImage.objects.order_by("-created_at")
        for instance in queryset:
            if instance.get_serving_url():
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
        return cast(QuerySet[MainPageLocation], MainPageLocation.objects.ready_for_main_page())


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
        country_slug: str,
        place_slug: str,
        date_slug: str,
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
        """
        Returns tag statistics, optionally filtered by category
        or limited to 'latest' filters.
        """
        category_filter: str | None = request.query_params.get("filter")
        latest: bool = request.query_params.get("latest", "false").lower() == "true"
        tags: QuerySet[Tag] = Tag.objects.with_stats(category_filter, latest=latest)

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
        categories: list[str] = [choice[0] for choice in CELESTIAL_OBJECT_CHOICES]
        return Response(categories)


class AstroImageSecureView(SecureMediaView):
    def get_object(self) -> AstroImage:
        slug: str = str(self.kwargs.get("slug"))
        return get_object_or_404(AstroImage, slug=slug)

    def get_file_path(self, obj: Model) -> str:
        assert isinstance(obj, AstroImage)
        # The public secure image endpoint is used by the frontend to fetch the
        # highest-quality asset for slug-addressable astro images.
        serving_field = obj.original_webp_field or obj.original_field
        return str(serving_field or "")

    def get_signature_id(self) -> str:
        return str(self.kwargs.get("slug", ""))


class AstroImageAdminSecureMediaView(GenericAdminSecureMediaView):
    """
    Dedicated admin media view for AstroImage to ease debugging.
    """

    def get_object(self) -> Model:
        return get_object_or_404(AstroImage, pk=self.kwargs.get("pk"))

    def get_signature_id(self) -> str:
        pk = self.kwargs.get("pk")
        field = self.kwargs.get("field_name")
        return f"admin_media_astrophotography_astroimage_{pk}_{field}"


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
        ids_param: str | None = request.query_params.get("ids")
        if ids_param:
            # Split comma-separated UUIDs
            ids: list[str] = [x.strip() for x in ids_param.split(",") if x.strip()]
            if ids:
                queryset = queryset.filter(pk__in=ids)

        url_mapping: dict[str, str] = {}

        for image in queryset:
            url_path: str = reverse("secure-image-file", kwargs={"slug": image.slug})
            params: dict[str, Any] = generate_signed_url_params(
                image.slug, expiration_seconds=settings.SECURE_MEDIA_URL_EXPIRATION
            )
            # Use PK as key to avoid language/translation mismatches
            # Use absolute URL from request context
            url_mapping[str(image.pk)] = (
                f"{request.build_absolute_uri(url_path)}?s={params['s']}&e={params['e']}"
            )

        return Response(url_mapping)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """
        Returns signed URL for a single image.
        """
        slug: str | None = pk
        image: AstroImage = get_object_or_404(AstroImage, slug=slug)
        url_path: str = reverse("secure-image-file", kwargs={"slug": image.slug})
        params: dict[str, Any] = generate_signed_url_params(
            image.slug, expiration_seconds=settings.SECURE_MEDIA_URL_EXPIRATION
        )
        signed_url: str = f"{request.build_absolute_uri(url_path)}?s={params['s']}&e={params['e']}"

        return Response({"url": signed_url})
