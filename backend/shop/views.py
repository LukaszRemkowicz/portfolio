import logging

from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from django.urls import reverse
from django.utils.decorators import method_decorator

from astrophotography.models import AstroImage
from common.decorators.cache import cache_response
from core.models import LandingPageSettings

from .models import ShopProduct, ShopSettings
from .serializers import ShopProductSerializer, ShopSettingsSerializer

logger = logging.getLogger(__name__)


class ShopProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public ViewSet for shop products.
    """

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]
    queryset = (
        ShopProduct.objects.filter(is_active=True)
        .select_related("image")
        .prefetch_related("translations")
        .order_by("-created_at")
    )
    serializer_class = ShopProductSerializer

    def _shop_unavailable_response(self) -> Response | None:
        settings_obj = LandingPageSettings.get_current()
        if settings_obj and settings_obj.shop_enabled:
            return None
        return Response(
            {"detail": "Shop is currently not available."},
            status=status.HTTP_404_NOT_FOUND,
        )

    @method_decorator(
        cache_response(
            timeout=settings.INFINITE_CACHE_TIMEOUT,
            key_prefix="api_cache_shop",
        )
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        unavailable_response = self._shop_unavailable_response()
        if unavailable_response is not None:
            return unavailable_response
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        products = page if page is not None else queryset
        product_serializer = self.get_serializer(products, many=True)
        settings_obj = ShopSettings.get_current()
        settings_payload = (
            ShopSettingsSerializer(settings_obj, context={"request": request}).data
            if settings_obj
            else {"title": "", "description": ""}
        )
        payload = {
            **settings_payload,
            "products": product_serializer.data,
        }
        if page is not None:
            return self.get_paginated_response(payload)
        return Response(payload)

    @method_decorator(
        cache_response(
            timeout=settings.INFINITE_CACHE_TIMEOUT,
            key_prefix="api_cache_shop",
        )
    )
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        unavailable_response = self._shop_unavailable_response()
        if unavailable_response is not None:
            return unavailable_response
        return super().retrieve(request, *args, **kwargs)


class ShopAstroImageLookupView(APIView):
    """
    Dedicated lookup view FOR THE SHOP only.
    Prioritizes the thumbnail field for fast cropping sources.
    This is isolated to avoid touching the shared gallery/astrophotography API.
    """

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]
    queryset = AstroImage.objects.all().only("pk", "thumbnail", "original_image", "path", "slug")

    def _get_lookup_url(self, request: Request, image: AstroImage) -> str:
        if image.thumbnail:
            return request.build_absolute_uri(image.thumbnail.url)

        if image.original_image:
            logger.info(
                "Shop image lookup fell back to AstroImage original image",
                extra={"image_id": image.pk},
            )
            return request.build_absolute_uri(image.original_image.url)

        logger.info(
            "Shop image lookup fell back to secure AstroImage serve route",
            extra={"image_id": image.pk, "slug": image.slug},
        )
        url_path = reverse("secure-image-file", kwargs={"slug": image.slug})
        return request.build_absolute_uri(url_path)

    def get(self, request: Request) -> Response:
        """
        Return the serving URL for a single AstroImage by its ID.
        Prioritizes the thumbnail for fast cropping.
        """
        id_param: str | None = request.query_params.get("id")
        if not id_param:
            return Response({"error": "Missing 'id' parameter"}, status=400)
        try:
            image = self.queryset.get(pk=id_param)
        except (AstroImage.DoesNotExist, ValueError):
            return Response({"error": "Image not found"}, status=404)

        return Response({"url": self._get_lookup_url(request, image)})
