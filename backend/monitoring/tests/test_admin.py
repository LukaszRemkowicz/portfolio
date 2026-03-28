import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from common.utils.signing import generate_signed_url_params
from monitoring.models import LogAnalysis
from monitoring.tests.factories import LogAnalysisFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_client() -> APIClient:
    User = get_user_model()
    admin_user = User.objects.create_superuser("admin_test@test.com", "password")
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def log_analysis() -> LogAnalysis:
    log_content = b"Error log data"
    log_file = SimpleUploadedFile("backend.log", log_content, content_type="text/plain")
    return LogAnalysisFactory.create(
        summary="Test summary",
        key_findings=["Test findings"],
        recommendations="Test recommendations",
        backend_logs=log_file,
        analysis_date=timezone.now().date(),
        severity="INFO",
    )


@pytest.mark.django_db
class TestLogAnalysisAdminSecureMediaView:
    def test_admin_secure_media_view_success_staff(
        self, admin_client: APIClient, log_analysis: LogAnalysis
    ) -> None:
        url: str = reverse(
            "admin-loganalysis-secure-media",
            kwargs={"pk": str(log_analysis.pk), "field_name": "backend_logs"},
        )
        sig_id: str = f"admin_media_monitoring_loganalysis_{log_analysis.pk}_backend_logs"
        params: dict[str, str] = generate_signed_url_params(sig_id)
        response = admin_client.get(url, params)
        assert response.status_code == status.HTTP_200_OK
        assert "X-Accel-Redirect" in response
        assert response["X-Accel-Redirect"] == f"/protected_media/{log_analysis.backend_logs.name}"

    def test_admin_secure_media_view_forbidden_anonymous(
        self, api_client: APIClient, log_analysis: LogAnalysis
    ) -> None:
        url: str = reverse(
            "admin-loganalysis-secure-media",
            kwargs={"pk": str(log_analysis.pk), "field_name": "backend_logs"},
        )
        sig_id: str = f"admin_media_monitoring_loganalysis_{log_analysis.pk}_backend_logs"
        params: dict[str, str] = generate_signed_url_params(sig_id)
        response = api_client.get(url, params)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_secure_media_view_missing_signature_staff(
        self, admin_client: APIClient, log_analysis: LogAnalysis
    ) -> None:
        url: str = reverse(
            "admin-loganalysis-secure-media",
            kwargs={"pk": str(log_analysis.pk), "field_name": "backend_logs"},
        )
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
