from django.db.models import Model
from django.shortcuts import get_object_or_404

from core.views import GenericAdminSecureMediaView

from .models import AstroImage


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
