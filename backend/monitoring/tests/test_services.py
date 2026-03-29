import logging
from datetime import date, timedelta
from unittest.mock import mock_open

import pytest

from django.test import override_settings

from common.llm.providers import MockLLMProvider
from monitoring.models import LogAnalysis
from monitoring.monitoring_agent_runner import MonitoringToolLoopRunner
from monitoring.services import (
    DockerLogCollector,
    HistoricalContextBuilder,
    LogAnalysisOrchestrator,
    LogAnalyzer,
    LogCleanupService,
    LogReportPreparationService,
    LogStorageService,
    MonitoringAgentLogOrchestrator,
    SitemapAnalysisOrchestrator,
    SitemapAnalysisStorageService,
    SitemapSummaryService,
)
from monitoring.sitemap_services import SitemapAuditService
from monitoring.tests.factories import LogAnalysisFactory
from monitoring.types import (
    LogReportResult,
    MonitoringAgentEventType,
    MonitoringAgentTraceEvent,
    MonitoringToolLoopResult,
    SitemapIssue,
    SitemapIssueCategory,
    SitemapReportResult,
)


@pytest.mark.django_db
class TestDockerLogCollector:
    def test_collect_logs_success(self, tmp_path, settings):
        """Test successful log retrieval from volume-mounted files."""
        settings.DOCKER_LOGS_DIR = str(tmp_path)
        (tmp_path / "backend.log").write_text("backend log content")
        (tmp_path / "frontend.log").write_text("frontend log content")
        (tmp_path / "nginx.log").write_text("nginx log content")
        (tmp_path / "traefik.log").write_text("traefik log content")
        (tmp_path / "collected_at.txt").write_text("2026-03-01T00:00:00Z")

        log_paths = DockerLogCollector.collect_logs()

        assert log_paths["backend"] == str(tmp_path / "backend.log")
        assert log_paths["frontend"] == str(tmp_path / "frontend.log")
        assert log_paths["nginx"] == str(tmp_path / "nginx.log")
        assert log_paths["traefik"] == str(tmp_path / "traefik.log")

    def test_collect_logs_missing_backend_raises(self, tmp_path, settings):
        """FileNotFoundError when backend.log is missing."""
        settings.DOCKER_LOGS_DIR = str(tmp_path)

        with pytest.raises(FileNotFoundError, match="backend.log"):
            DockerLogCollector.collect_logs()

    def test_collect_logs_missing_nginx_warns_but_succeeds(self, tmp_path, settings, caplog):
        """nginx.log missing -> warns and returns None for nginx_path, does NOT raise."""

        settings.DOCKER_LOGS_DIR = str(tmp_path)
        (tmp_path / "backend.log").write_text("backend log content")
        (tmp_path / "collected_at.txt").write_text("2026-03-01T00:00:00Z")
        # nginx.log intentionally NOT created

        with caplog.at_level(logging.WARNING, logger="monitoring.services"):
            log_paths = DockerLogCollector.collect_logs()

        assert log_paths["backend"] == str(tmp_path / "backend.log")
        assert log_paths["frontend"] is None
        assert log_paths["nginx"] is None
        assert log_paths["traefik"] is None
        assert any(
            "nginx" in record.message.lower()
            or "frontend" in record.message.lower()
            or "traefik" in record.message.lower()
            for record in caplog.records
        )

    def test_check_staleness_warns_when_old(self, tmp_path, settings, caplog):
        """Warning logged when logs are older than MAX_STALENESS_HOURS."""

        settings.DOCKER_LOGS_DIR = str(tmp_path)
        (tmp_path / "backend.log").write_text("log")
        (tmp_path / "collected_at.txt").write_text("2000-01-01T00:00:00Z")

        with caplog.at_level(logging.WARNING, logger="monitoring.services"):
            DockerLogCollector.collect_logs()

        assert any("hours old" in record.message for record in caplog.records)


@pytest.mark.django_db
class TestLogCleanupService:
    def test_cleanup_old_logs(self):
        """Test that old logs are deleted."""
        # Create some old and new logs using Factory
        old_log = LogAnalysisFactory.create(analysis_date=date(2020, 1, 1), summary="Old")
        new_log = LogAnalysisFactory.create(analysis_date=date.today(), summary="New")

        # Delete anything older than 30 days
        LogCleanupService.cleanup_old_logs(days_to_keep=30)

        assert LogAnalysis.objects.filter(pk=new_log.pk).exists()
        # The old log is definitely older than 30 days from now
        assert not LogAnalysis.objects.filter(pk=old_log.pk).exists()


@pytest.mark.django_db
class TestLogStorageService:
    def test_create_or_replace_analysis_creates_new(self):
        """Test creating a new analysis record."""
        analysis = LogStorageService.create_or_replace_analysis(
            analysis_date=date.today(),
            summary="Test summary",
            severity="INFO",
        )

        assert analysis is not None
        assert analysis.summary == "Test summary"
        assert analysis.severity == "INFO"
        assert LogAnalysis.objects.count() == 1

    def test_create_or_replace_analysis_replaces_existing(self):
        """Test that creating analysis for same date replaces existing."""
        # Create first record
        LogAnalysisFactory.create(analysis_date=date.today(), summary="First")
        assert LogAnalysis.objects.count() == 1

        # Create second record for same date
        analysis = LogStorageService.create_or_replace_analysis(
            analysis_date=date.today(),
            summary="Second",
            severity="WARNING",
        )

        assert LogAnalysis.objects.count() == 1  # Still only 1
        assert analysis.summary == "Second"
        assert analysis.severity == "WARNING"


class TestLogReportPreparationService:
    def test_prepare_report_from_files_returns_typed_result(self, mocker, mock_llm_response):
        mock_agent = mocker.MagicMock()
        mock_agent.analyze_logs_from_files.return_value = mock_llm_response
        analyzer = LogAnalyzer(mock_agent)
        service = LogReportPreparationService(analyzer)

        report = service.prepare_report_from_files(
            {"backend": "/tmp/backend.log"},
            collected_at="2026-03-05T12:00:00Z",
            historical_context="prior context",
        )

        assert report.summary == mock_llm_response["summary"]
        assert report.severity == mock_llm_response["severity"]
        assert report.gpt_tokens_used == mock_llm_response["gpt_tokens_used"]
        assert report.gpt_cost_usd == mock_llm_response["gpt_cost_usd"]


class TestMonitoringAgentLogOrchestrator:
    def test_run_monitoring_agent_prefers_final_payload_over_deterministic_report(self, mocker):
        mock_agent = mocker.MagicMock()
        analyzer = LogAnalyzer(mock_agent)
        runner = mocker.MagicMock(spec=MonitoringToolLoopRunner)
        runner.run.return_value = MonitoringToolLoopResult(
            summary="Agent summary",
            findings=["Agent finding"],
            trace=[
                MonitoringAgentTraceEvent(
                    event_type=MonitoringAgentEventType.START,
                    message="starting job=log_report",
                )
            ],
            final_payload={
                "summary": "Agent summary",
                "severity": "CRITICAL",
                "key_findings": ["Agent finding"],
                "recommendations": "Review nginx logs.",
                "trend_summary": "New today.",
            },
            stop_reason="final_report",
        )
        orchestrator = MonitoringAgentLogOrchestrator(
            collector=DockerLogCollector(),
            analyzer=analyzer,
            storage=LogStorageService(),
            agent_runner=runner,
        )

        deterministic_report = LogReportResult(
            summary="Deterministic summary",
            severity="WARNING",
            key_findings=["Deterministic finding"],
            recommendations="Deterministic recommendation",
            trend_summary="Stable.",
            gpt_tokens_used=10,
            gpt_cost_usd=0.001,
        )

        result = orchestrator._run_monitoring_agent(deterministic_report)

        assert result.summary == "Agent summary"
        assert result.severity == "CRITICAL"
        assert result.key_findings == ["Agent finding"]

    def test_run_monitoring_agent_falls_back_to_deterministic_report(self, mocker):
        mock_agent = mocker.MagicMock()
        analyzer = LogAnalyzer(mock_agent)
        runner = mocker.MagicMock(spec=MonitoringToolLoopRunner)
        runner.run.return_value = MonitoringToolLoopResult(
            summary="Deterministic summary",
            findings=["Deterministic finding"],
            trace=[],
            final_payload={"summary": "Deterministic summary"},
            stop_reason="final_report",
        )
        orchestrator = MonitoringAgentLogOrchestrator(
            collector=DockerLogCollector(),
            analyzer=analyzer,
            storage=LogStorageService(),
            agent_runner=runner,
        )

        deterministic_report = LogReportResult(
            summary="Deterministic summary",
            severity="WARNING",
            key_findings=["Deterministic finding"],
            recommendations="Deterministic recommendation",
            trend_summary="Stable.",
            gpt_tokens_used=10,
            gpt_cost_usd=0.001,
        )

        result = orchestrator._run_monitoring_agent(deterministic_report)

        assert result.severity == "WARNING"
        assert result.recommendations == "Deterministic recommendation"


class TestSitemapSummaryService:
    def test_summarize_returns_llm_summary(self):
        provider = MockLLMProvider()
        provider.configure(
            mock_response=(
                '{"summary":"Sitemap has one broken URL.","severity":"WARNING",'
                '"key_findings":["broken_url: 1"],'
                '"recommendations":"Fix the broken URL.",'
                '"trend_summary":"New issue detected."}'
            ),
            mock_usage={"total_tokens": 44, "cost_usd": 0.0012},
        )
        service = SitemapSummaryService(provider=provider)
        report = SitemapReportResult(
            root_sitemap_url="https://portfolio.example/sitemap.xml",
            total_sitemaps=1,
            total_urls=3,
            issues=[
                SitemapIssue(
                    url="https://portfolio.example/missing",
                    category=SitemapIssueCategory.BROKEN_URL,
                    message="URL returned an error status.",
                    status_code=404,
                )
            ],
        )

        result = service.summarize(report)

        assert result.summary == "Sitemap has one broken URL."
        assert result.severity == "WARNING"
        assert result.gpt_tokens_used == 44
        assert result.gpt_cost_usd == 0.0012


@pytest.mark.django_db
class TestSitemapAnalysisStorageService:
    def test_create_or_replace_analysis_stores_sitemap_results(self):
        report = SitemapReportResult(
            root_sitemap_url="https://portfolio.example/sitemap.xml",
            total_sitemaps=2,
            total_urls=20,
            issues=[
                SitemapIssue(
                    url="https://portfolio.example/missing",
                    category=SitemapIssueCategory.BROKEN_URL,
                    message="URL returned an error status.",
                    status_code=404,
                )
            ],
        )
        summary = SitemapSummaryService(provider=MockLLMProvider())._build_fallback_summary(report)

        analysis = SitemapAnalysisStorageService.create_or_replace_analysis(
            analysis_date=date.today(),
            report=report,
            summary=summary,
            execution_time_seconds=4.0,
        )

        assert analysis.total_sitemaps == 2
        assert analysis.issue_summary["broken_url"] == 1
        assert analysis.key_findings


class TestSitemapAnalysisOrchestrator:
    @pytest.mark.django_db
    def test_analyze_and_store_creates_sitemap_analysis(self, mocker):
        report = SitemapReportResult(
            root_sitemap_url="https://portfolio.example/sitemap.xml",
            total_sitemaps=1,
            total_urls=2,
            issues=[],
        )
        audit_service = mocker.MagicMock(spec=SitemapAuditService)
        audit_service.audit.return_value = report
        audit_service.get_default_sitemap_url.return_value = "https://portfolio.example/sitemap.xml"

        summary_service = mocker.MagicMock(spec=SitemapSummaryService)
        summary_service.summarize.return_value = SitemapSummaryService(
            provider=MockLLMProvider()
        )._build_fallback_summary(report)

        orchestrator = SitemapAnalysisOrchestrator(
            audit_service=audit_service,
            summary_service=summary_service,
            storage=SitemapAnalysisStorageService(),
        )

        analysis = orchestrator.analyze_and_store(date.today())

        assert analysis.total_urls == 2
        assert analysis.root_sitemap_url == "https://portfolio.example/sitemap.xml"


@pytest.mark.django_db
class TestLogAnalysisOrchestrator:
    def test_analyze_and_store_creates_record(self, mocker, mock_llm_response):
        """Test the full analysis flow creates a record."""
        # Override settings for this test
        with override_settings(ENVIRONMENT="test"):
            # Mocks
            mock_collector = mocker.patch("monitoring.services.DockerLogCollector.collect_logs")
            mock_agent = mocker.MagicMock()

            mock_collector.return_value = {
                "backend": "/tmp/backend.log",
                "frontend": "/tmp/frontend.log",
                "nginx": None,
                "traefik": "/tmp/traefik.log",
            }
            mock_agent.analyze_logs_from_files.return_value = mock_llm_response

            # Mock file operations to prevent reading/writing real files in /tmp
            mocker.patch("builtins.open", mock_open(read_data="Mock logs"))
            mocker.patch("os.remove")
            mocker.patch("os.path.exists", return_value=True)
            mocker.patch("os.path.getsize", return_value=100)
            mocker.patch("django.db.models.fields.files.FieldFile.save")

            # Create orchestrator with mocked dependencies
            analyzer = LogAnalyzer(mock_agent)
            orchestrator = LogAnalysisOrchestrator(
                collector=DockerLogCollector(),
                analyzer=analyzer,
                storage=LogStorageService(),
            )

            record = orchestrator.analyze_and_store(analysis_date=date.today())

        assert record is not None
        assert record.summary == mock_llm_response["summary"]
        assert record.severity == mock_llm_response["severity"]
        assert record.gpt_tokens_used == mock_llm_response["gpt_tokens_used"]
        assert LogAnalysis.objects.count() == 1

    @pytest.mark.django_db
    def test_analyze_and_store_idempotency(self, mocker, mock_llm_response):
        """Test that re-running analysis for same day replaces the record."""
        with override_settings(ENVIRONMENT="test"):
            # Mocks
            mock_collector = mocker.patch("monitoring.services.DockerLogCollector.collect_logs")
            mock_agent = mocker.MagicMock()

            mock_collector.return_value = {
                "backend": "/tmp/backend.log",
                "frontend": "/tmp/frontend.log",
                "nginx": None,
                "traefik": "/tmp/traefik.log",
            }
            mock_agent.analyze_logs_from_files.return_value = mock_llm_response

            mocker.patch("builtins.open", mock_open(read_data="Mock logs"))
            mocker.patch("os.remove")
            mocker.patch("os.path.exists", return_value=True)
            mocker.patch("os.path.getsize", return_value=100)
            mocker.patch("django.db.models.fields.files.FieldFile.save")

            # Create orchestrator
            analyzer = LogAnalyzer(mock_agent)
            orchestrator = LogAnalysisOrchestrator(
                collector=DockerLogCollector(),
                analyzer=analyzer,
                storage=LogStorageService(),
            )

            # First run
            orchestrator.analyze_and_store(date.today())
            assert LogAnalysis.objects.count() == 1

            # Second run
            orchestrator.analyze_and_store(date.today())
            assert LogAnalysis.objects.count() == 1  # Should still be 1, not 2


@pytest.mark.django_db
class TestHistoricalContextBuilder:
    """Tests for HistoricalContextBuilder formatting service."""

    def test_build_returns_empty_string_when_no_history(self):
        """Empty DB → empty string, no crash."""
        result = HistoricalContextBuilder.build()
        assert result == ""

    def test_build_excludes_given_date(self):
        """Today's record is excluded when exclude_date=date.today()."""
        LogAnalysisFactory(analysis_date=date.today(), summary="Today's summary")
        result = HistoricalContextBuilder.build(exclude_date=date.today())
        assert result == ""

    def test_build_formats_records_as_markdown(self):
        """Records are formatted with date, severity, summary, findings, recommendations."""
        LogAnalysisFactory(
            analysis_date=date.today() - timedelta(days=1),
            summary="All good",
            severity="INFO",
            key_findings=["No anomalies"],
            recommendations="None needed",
        )

        result = HistoricalContextBuilder.build(exclude_date=date.today())

        assert "All good" in result
        assert "INFO" in result
        assert "No anomalies" in result
        assert "None needed" in result

    def test_build_includes_multiple_records(self):
        """Multiple records within 5-day window are all included in output."""
        LogAnalysisFactory(analysis_date=date.today() - timedelta(days=1), summary="Day minus 1")
        LogAnalysisFactory(analysis_date=date.today() - timedelta(days=2), summary="Day minus 2")

        result = HistoricalContextBuilder.build(exclude_date=date.today())
        assert "Day minus 1" in result
        assert "Day minus 2" in result

    def test_build_excludes_records_older_than_5_days(self):
        """Records older than 5 days are not included."""
        LogAnalysisFactory(analysis_date=date.today() - timedelta(days=6), summary="Too old")

        result = HistoricalContextBuilder.build()
        assert "Too old" not in result


@pytest.mark.django_db
class TestOrchestratorHistoricalContextWiring:
    """Test that historical context is fetched and passed to the analyzer."""

    def test_historical_context_passed_to_analyzer(self, mocker, mock_llm_response):
        """orchestrator calls HistoricalContextBuilder.build() and passes result to analyzer."""

        with override_settings(ENVIRONMENT="test"):
            mock_collector = mocker.patch("monitoring.services.DockerLogCollector.collect_logs")
            mock_agent = mocker.MagicMock()
            mock_builder = mocker.patch(
                "monitoring.services.HistoricalContextBuilder.build",
                return_value="## 2026-03-08 — Severity: INFO\nSummary: All calm",
            )

            mock_collector.return_value = ("/tmp/backend.log", "/tmp/frontend.log", None)
            mock_agent.analyze_logs_from_files.return_value = mock_llm_response

            mocker.patch("builtins.open", mock_open(read_data="Mock logs"))
            mocker.patch("os.remove")
            mocker.patch("os.path.exists", return_value=True)
            mocker.patch("os.path.getsize", return_value=100)
            mocker.patch("django.db.models.fields.files.FieldFile.save")

            analyzer = LogAnalyzer(mock_agent)
            orchestrator = LogAnalysisOrchestrator(
                collector=DockerLogCollector(),
                analyzer=analyzer,
                storage=LogStorageService(),
            )
            orchestrator.analyze_and_store(date.today())

            # Builder was called with today excluded
            mock_builder.assert_called_once_with(exclude_date=date.today())

            # Historical context was forwarded to the agent
            call_kwargs = mock_agent.analyze_logs_from_files.call_args.kwargs
            assert "historical_context" in call_kwargs
            assert "All calm" in call_kwargs["historical_context"]
