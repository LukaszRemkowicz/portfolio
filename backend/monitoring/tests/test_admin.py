import pytest
from bs4 import BeautifulSoup
from celery.result import AsyncResult
from pytest_mock import MockerFixture
from rest_framework import status

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from common.utils.signing import generate_signed_url_params
from monitoring.admin import SitemapAnalysisAdmin
from monitoring.models import LogAnalysis, SitemapAnalysis
from monitoring.tasks import daily_sitemap_analysis_task
from monitoring.tests.factories import LogAnalysisFactory, SitemapAnalysisFactory


@pytest.fixture
def api_client() -> Client:
    return Client()


@pytest.fixture
def admin_client() -> Client:
    User = get_user_model()
    admin_user = User.objects.create_superuser("admin_test@test.com", "password")
    client = Client()
    client.force_login(admin_user)
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
        self, admin_client: Client, log_analysis: LogAnalysis
    ) -> None:
        url: str = reverse(
            "admin-loganalysis-secure-media",
            kwargs={"pk": str(log_analysis.pk), "field_name": "backend_logs"},
        )
        sig_id: str = f"admin_media_monitoring_loganalysis_{log_analysis.pk}_backend_logs"
        params: dict[str, str] = generate_signed_url_params(sig_id)
        response = admin_client.get(url, params)
        assert response.status_code == 200
        assert "X-Accel-Redirect" in response
        assert response["X-Accel-Redirect"] == f"/protected_media/{log_analysis.backend_logs.name}"

    def test_admin_secure_media_view_forbidden_anonymous(
        self, api_client: Client, log_analysis: LogAnalysis
    ) -> None:
        url: str = reverse(
            "admin-loganalysis-secure-media",
            kwargs={"pk": str(log_analysis.pk), "field_name": "backend_logs"},
        )
        sig_id: str = f"admin_media_monitoring_loganalysis_{log_analysis.pk}_backend_logs"
        params: dict[str, str] = generate_signed_url_params(sig_id)
        response = api_client.get(url, params)
        assert response.status_code == 404

    def test_admin_secure_media_view_missing_signature_staff(
        self, admin_client: Client, log_analysis: LogAnalysis
    ) -> None:
        url: str = reverse(
            "admin-loganalysis-secure-media",
            kwargs={"pk": str(log_analysis.pk), "field_name": "backend_logs"},
        )
        response = admin_client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestSitemapAnalysisAdmin:
    def test_issue_count_and_summary_helpers(self) -> None:
        sitemap_analysis: SitemapAnalysis = SitemapAnalysisFactory(
            issue_summary={"broken_url": 2, "canonical_mismatch": 1},
            issues=[{"url": "a"}, {"url": "b"}, {"url": "c"}],
        )
        admin_site = AdminSite()
        admin_instance = SitemapAnalysisAdmin(SitemapAnalysis, admin_site)

        assert admin_instance.issue_count(sitemap_analysis) == 3
        assert admin_instance.issue_summary_pretty(sitemap_analysis) == (
            "broken url: 2\ncanonical mismatch: 1"
        )

    def test_changelist_shows_run_now_button_without_add_button(self, admin_client: Client) -> None:
        response: HttpResponse = admin_client.get(
            reverse("admin:monitoring_sitemapanalysis_changelist")
        )

        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        content = soup.get_text(" ", strip=True)
        assert "Run Sitemap Analysis Now" in content
        assert "Add Sitemap Analysis" not in content
        assert "Dodaj Sitemap Analysis" not in content

        run_now_selector = (
            "form#run-sitemap-analysis-now-form"
            "[action='/admin/monitoring/sitemapanalysis/run-now/']"
        )
        run_now_form = soup.select_one(run_now_selector)
        assert run_now_form is not None
        status_root = soup.select_one("#sitemap-task-status")
        assert status_root is not None

    def test_run_now_view_queues_task_and_redirects(
        self, admin_client: Client, mocker: MockerFixture
    ) -> None:
        delay_mock = mocker.patch.object(daily_sitemap_analysis_task, "delay")
        delay_mock.return_value = AsyncResult("task-123")

        response: HttpResponse = admin_client.post(
            reverse("admin:monitoring_sitemapanalysis_run_now")
        )

        assert response.status_code == 302
        assert response.url == reverse("admin:monitoring_sitemapanalysis_changelist")
        session = admin_client.session
        assert session[SitemapAnalysisAdmin.SESSION_TASK_ID_KEY] == "task-123"
        delay_mock.assert_called_once()
        kwargs = delay_mock.call_args.kwargs
        assert kwargs["analysis_date"] == timezone.localdate().isoformat()


@pytest.mark.django_db
class TestSitemapTaskStatusView:
    def test_returns_success_payload_for_finished_task(
        self, admin_client: Client, mocker: MockerFixture
    ) -> None:
        async_result = mocker.MagicMock()
        async_result.status = "SUCCESS"
        async_result.successful.return_value = True
        async_result.failed.return_value = False
        async_result.result = {
            "sitemap_analysis_id": 17,
            "severity": "INFO",
        }
        mocker.patch("monitoring.views.AsyncResult", return_value=async_result)

        response = admin_client.get(
            reverse("admin-sitemap-analysis-task-status", kwargs={"task_id": "task-123"})
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        assert response.json()["progress_percent"] == 100
        assert response.json()["sitemap_analysis_id"] == 17

    def test_returns_running_payload_for_started_task(
        self, admin_client: Client, mocker: MockerFixture
    ) -> None:
        async_result = mocker.MagicMock()
        async_result.status = "STARTED"
        async_result.successful.return_value = False
        async_result.failed.return_value = False
        async_result.result = None
        mocker.patch("monitoring.views.AsyncResult", return_value=async_result)

        response = admin_client.get(
            reverse("admin-sitemap-analysis-task-status", kwargs={"task_id": "task-456"})
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "running"
        assert response.json()["complete"] is False
