import logging

from django.db.models import Model
from django.shortcuts import get_object_or_404

from core.views import GenericAdminSecureMediaView

from .models import LogAnalysis

logger = logging.getLogger(__name__)


class LogAnalysisAdminSecureMediaView(GenericAdminSecureMediaView):
    """
    Dedicated admin media view for LogAnalysis to ease debugging.
    """

    def get_object(self) -> Model:
        return get_object_or_404(LogAnalysis, pk=self.kwargs.get("pk"))

    def get_signature_id(self) -> str:
        pk = self.kwargs.get("pk")
        field = self.kwargs.get("field_name")
        return f"admin_media_monitoring_loganalysis_{pk}_{field}"
