import pytest

from django.core import mail

from common.llm.providers import MockLLMProvider
from monitoring.models import LogAnalysis
from monitoring.tasks import (
    cleanup_old_logs_task,
    daily_log_analysis_task,
    daily_monitoring_agent_log_task,
    daily_sitemap_analysis_task,
)
from monitoring.tests.factories import SitemapAnalysisFactory


@pytest.mark.django_db
class TestMonitoringTasks:

    def test_daily_log_analysis_task_orchestration(self, mocker, log_analysis):
        """Test that the orchestrator task coordinates analysis and email sending."""
        mocker.patch("monitoring.tasks.settings.RUN_LEGACY_DAILY_TASK", True)

        # Setup mocks
        mock_orchestrator = mocker.MagicMock()
        mock_create_default = mocker.patch(
            "monitoring.services.LogAnalysisOrchestrator.create_default"
        )
        mock_create_default.return_value = mock_orchestrator

        mock_email_service_cls = mocker.patch("monitoring.tasks.LogAnalysisEmailService")
        mock_email_service_instance = mock_email_service_cls.return_value

        # Ensure fixture state
        log_analysis.email_sent = False
        log_analysis.save()

        mock_orchestrator.analyze_and_store.return_value = log_analysis

        # Execute task
        result = daily_log_analysis_task()

        # Verify orchestrator was created
        mock_create_default.assert_called_once()

        # Verify analysis was called
        mock_orchestrator.analyze_and_store.assert_called_once()

        # Verify email service was instantiated and called
        mock_email_service_cls.assert_called_once_with(log_analysis)
        mock_email_service_instance.send_email.assert_called_once()

        # Verify email_sent flag was updated in DB
        log_analysis.refresh_from_db()
        assert log_analysis.email_sent is True

        # Verify return value
        assert result["status"] == "success"
        assert result["log_analysis_id"] == log_analysis.id

    def test_daily_log_analysis_integration(self, mocker, settings):
        """
        True End-to-End Integration test.
        Mocks ONLY:
        - DockerLogCollector (we don't have containers in test)
        - OpenAI API call (uses our new dynamic MockLLMProvider)
        - File System (os.open/getsize for reading/saving logs)

        Verifies: Data is processed -> DB is populated correctly -> Email renders and sends.
        """
        mocker.patch("monitoring.tasks.settings.RUN_LEGACY_DAILY_TASK", True)

        # 1. Configure the LLM mock to return the attack sequence
        # We read the file FIRST before we mock `builtins.open` below to prevent I/O conflicts.
        attack_json_path = settings.BASE_DIR / "monitoring/tests/llm_responses/attack.json"
        with open(attack_json_path, "r", encoding="utf-8") as f:
            attack_json = f.read()

        provider = MockLLMProvider()
        provider.configure(
            mock_response=attack_json,
            mock_usage={
                "completion_tokens": 50,
                "prompt_tokens": 100,
                "total_tokens": 150,
                "cost_usd": 0.0075,
            },
        )
        mocker.patch("monitoring.services.LLMProviderRegistry.get", return_value=provider)

        # 2. Mock the log collection I/O
        mock_collector = mocker.patch("monitoring.services.DockerLogCollector")
        collector_instance = mock_collector.return_value
        collector_instance.collect_logs.return_value = {
            "backend": "/tmp/be.log",
            "frontend": "/tmp/fe.log",
            "nginx": "/tmp/nx.log",
            "traefik": "/tmp/traefik.log",
        }
        collector_instance.get_collected_at.return_value = "2026-03-05T12:00:00Z"

        # Mock reading of log files specifically in the agent, not globally
        mocker.patch("monitoring.agent.agent.open", mocker.mock_open(read_data="Mock log line"))
        mocker.patch("os.path.getsize", return_value=100)

        # Mock the Django File saving so we don't dump files into the local /media during tests
        mocker.patch("monitoring.services.LogStorageService.attach_log_files")

        # 3. RUN PIPELINE
        result = daily_log_analysis_task()

        # 4. Assert Pipeline Status
        assert result["status"] == "success"

        # 5. Assert Database Persistence
        assert LogAnalysis.objects.count() == 1
        analysis = LogAnalysis.objects.first()

        # Verify the new fields and agent results were saved!
        assert analysis.severity == "CRITICAL"
        assert analysis.gpt_tokens_used == 150
        assert analysis.gpt_cost_usd == 0.0075
        assert analysis.email_sent is True
        assert "Automated reconnaissance" in analysis.summary

        # 6. Assert Email rendering and dispatch
        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        # Check subject template
        assert "CRITICAL" in email.subject
        assert str(analysis.analysis_date) in email.subject

        # Check body rendering (specifically the findings array)
        # The attack.json contains these specific findings
        assert "A05 Security Misconfiguration" in email.body
        assert "A01 Broken Access Control" in email.body
        assert "$0.0075" in email.body  # The template should render the new cost tracking!

    def test_cleanup_old_logs_task(self, mocker):
        """Test that the cleanup task calls the service."""
        mock_cleanup = mocker.patch("monitoring.services.LogCleanupService.cleanup_old_logs")
        mock_cleanup.return_value = 5  # 5 records deleted

        # Execute task
        result = cleanup_old_logs_task(days_to_keep=20)

        # Verify
        mock_cleanup.assert_called_once_with(20)
        assert result["status"] == "success"
        assert result["deleted_count"] == 5

    def test_daily_monitoring_agent_log_task_orchestration(self, mocker, log_analysis):
        """Test that the monitoring-agent task coordinates analysis and email sending."""
        mock_orchestrator = mocker.MagicMock()
        mock_create_default = mocker.patch(
            "monitoring.tasks.MonitoringAgentLogOrchestrator.create_default"
        )
        mock_create_default.return_value = mock_orchestrator

        mock_email_service_cls = mocker.patch("monitoring.tasks.LogAnalysisEmailService")
        mock_email_service_instance = mock_email_service_cls.return_value

        log_analysis.email_sent = False
        log_analysis.save()

        mock_orchestrator.analyze_and_store.return_value = log_analysis

        result = daily_monitoring_agent_log_task()

        mock_create_default.assert_called_once()
        mock_orchestrator.analyze_and_store.assert_called_once()
        mock_email_service_cls.assert_called_once_with(log_analysis)
        mock_email_service_instance.send_email.assert_called_once()

        log_analysis.refresh_from_db()
        assert log_analysis.email_sent is True
        assert result["status"] == "success"
        assert result["runtime"] == "monitoring_agent"

    def test_daily_sitemap_analysis_task_orchestration(self, mocker):
        sitemap_analysis = SitemapAnalysisFactory(email_sent=False)
        mock_orchestrator = mocker.MagicMock()
        mock_create_default = mocker.patch(
            "monitoring.tasks.SitemapAnalysisOrchestrator.create_default"
        )
        mock_create_default.return_value = mock_orchestrator

        mock_email_service_cls = mocker.patch("monitoring.tasks.SitemapAnalysisEmailService")
        mock_email_service_instance = mock_email_service_cls.return_value
        mock_orchestrator.analyze_and_store.return_value = sitemap_analysis

        result = daily_sitemap_analysis_task()

        mock_create_default.assert_called_once()
        mock_orchestrator.analyze_and_store.assert_called_once()
        mock_email_service_cls.assert_called_once_with(sitemap_analysis)
        mock_email_service_instance.send_email.assert_called_once()

        sitemap_analysis.refresh_from_db()
        assert sitemap_analysis.email_sent is True
        assert result["status"] == "success"
        assert result["sitemap_analysis_id"] == sitemap_analysis.id
