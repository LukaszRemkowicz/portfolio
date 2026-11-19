import logging
import mimetypes

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.views import View

from astrophotography.models import AstroImage
from common.utils.signing import generate_signed_url_params

logger = logging.getLogger(__name__)


class ShopAstroImageLookupView(View):
    """
    Dedicated lookup view FOR THE SHOP only.
    Returns the original AstroImage source for the admin cropper.
    """

    queryset = AstroImage.objects.all().only("pk", "original", "slug")

    def _get_lookup_url(self, request: HttpRequest, image: AstroImage) -> str:
        if not image.original:
            return ""

        url_path = reverse(
            "admin-astroimage-secure-media",
            kwargs={"pk": str(image.pk), "field_name": "original"},
        )
        signature_id = f"admin_media_astrophotography_astroimage_{image.pk}_original"
        params = generate_signed_url_params(
            signature_id,
            expiration_seconds=settings.SECURE_MEDIA_URL_EXPIRATION,
        )
        return f"{request.build_absolute_uri(url_path)}?s={params['s']}&e={params['e']}"

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Return the serving URL for a single AstroImage by its ID.
        Uses the original source because the admin cropper should not crop
        from a compressed display variant.
        """
        # Same as the admin media views: hide the endpoint from non-staff.
        if not request.user.is_staff:
            return JsonResponse({"error": "Not found"}, status=404)
        id_param: str | None = request.GET.get("id")
        if not id_param:
            return JsonResponse({"error": "Missing 'id' parameter"}, status=400)
        try:
            image = self.queryset.get(pk=id_param)
        except AstroImage.DoesNotExist, ValueError:
            return JsonResponse({"error": "Image not found"}, status=404)

        url = self._get_lookup_url(request, image)
        if not url:
            return JsonResponse({"error": "Original image field is empty"}, status=404)
        source_name = str(image.original.name or "")
        mime_type = mimetypes.guess_type(source_name)[0] or "image/jpeg"
        return JsonResponse(
            {
                "url": url,
                "source_name": source_name,
                "mime_type": mime_type,
            }
        )
