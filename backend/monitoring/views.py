import logging

from celery.result import AsyncResult
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

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


class BaseMonitoringTaskStatusView(APIView):
    permission_classes = [IsAdminUser]
    result_type: str | None = None
    result_id_field: str | None = None

    def build_response(self, task_id: str) -> Response:
        async_result = AsyncResult(task_id)
        celery_status: str = async_result.status
        normalized_status, progress = self._normalize_status(celery_status)
        payload: dict[str, object] = {
            "task_id": task_id,
            "status": normalized_status,
            "celery_status": celery_status,
            "progress_percent": progress,
            "complete": normalized_status in {"success", "failed"},
        }

        if async_result.successful() and isinstance(async_result.result, dict):
            result_payload: dict[str, object] = async_result.result
            payload["result"] = result_payload
            if self.result_type is not None:
                payload["related_object_type"] = self.result_type
            if self.result_id_field is not None:
                payload["related_object_id"] = result_payload.get(self.result_id_field)
        elif async_result.failed():
            payload["error"] = str(async_result.result)

        return Response(payload)

    @staticmethod
    def _normalize_status(status: str) -> tuple[str, int]:
        if status == "SUCCESS":
            return "success", 100
        if status == "FAILURE":
            return "failed", 100
        if status == "STARTED":
            return "running", 70
        if status == "RETRY":
            return "running", 80
        return "queued", 25


class MonitoringTaskStatusView(BaseMonitoringTaskStatusView):
    TASK_KIND_CONFIG: dict[str, tuple[str, str]] = {
        "log": ("log_analysis", "log_analysis_id"),
        "sitemap": ("sitemap_analysis", "sitemap_analysis_id"),
    }

    def get(self, request, task_kind: str, task_id: str) -> Response:
        if task_kind not in self.TASK_KIND_CONFIG:
            return Response({"detail": "Unknown task kind."}, status=404)

        self.result_type, self.result_id_field = self.TASK_KIND_CONFIG[task_kind]
        return self.build_response(task_id)
