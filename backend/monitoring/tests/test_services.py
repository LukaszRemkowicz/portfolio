from datetime import date
from unittest.mock import mock_open

import pytest

from django.test import override_settings

from monitoring.models import LogAnalysis
from monitoring.services import LogCollectionService
from monitoring.tests.factories import LogAnalysisFactory


@pytest.mark.django_db
class TestLogCollectionService:
    def test_get_docker_logs_success(self, mocker):
        """Test successful docker log retrieval."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.stdout = "Log content"
        mock_run.return_value.returncode = 0

        # Mocks
        mocker.patch("shutil.which", return_value="/usr/bin/docker")
        mocker.patch("builtins.open", mock_open())
        mocker.patch("os.path.getsize", return_value=100)

        # Execute
        logs = LogCollectionService.collect_docker_logs()

        assert len(logs) == 2
        assert "backend" in logs[0]
        assert "frontend" in logs[1]
        assert "logs" in mock_run.call_args[0][0]
        assert "--tail=2000" in mock_run.call_args[0][0]

    def test_cleanup_old_logs(self):
        """Test that old logs are deleted."""
        # Create some old and new logs using Factory
        old_log = LogAnalysisFactory.create(analysis_date=date(2020, 1, 1), summary="Old")
        new_log = LogAnalysisFactory.create(analysis_date=date.today(), summary="New")

        # Override today for the test logic if needed, or just rely on date math
        # simplistic: delete anything older than 365 days
        LogCollectionService.cleanup_old_logs(days_to_keep=30)

        assert LogAnalysis.objects.filter(pk=new_log.pk).exists()
        # The old log is definitely older than 30 days from now
        assert not LogAnalysis.objects.filter(pk=old_log.pk).exists()

    def test_analyze_and_store_creates_record(self, mocker, mock_llm_response):
        """Test the full analysis flow creates a record."""
        # Override settings for this test
        with override_settings(ENVIRONMENT="test"):
            # Mocks
            mock_get_logs = mocker.patch(
                "monitoring.services.LogCollectionService.collect_docker_logs"
            )
            mock_agent = mocker.patch("monitoring.services.LogCollectionService.agent")

            mock_get_logs.return_value = ("/tmp/backend.log", "/tmp/frontend.log")

            # Mock agent response using JSON file
            mock_agent.analyze_logs_from_files.return_value = mock_llm_response

            # Mock file operations to prevent reading/writing real files in /tmp
            mocker.patch("builtins.open", mock_open(read_data="Mock logs"))
            mocker.patch("os.remove")
            mocker.patch("os.path.exists", return_value=True)
            mocker.patch("os.path.getsize", return_value=100)

            record = LogCollectionService.analyze_and_store(analysis_date=date.today())

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
            mock_get_logs = mocker.patch(
                "monitoring.services.LogCollectionService.collect_docker_logs"
            )
            mock_agent = mocker.patch("monitoring.services.LogCollectionService.agent")

            mock_get_logs.return_value = ("/tmp/backend.log", "/tmp/frontend.log")
            mock_agent.analyze_logs_from_files.return_value = mock_llm_response

            mocker.patch("builtins.open", mock_open(read_data="Mock logs"))
            mocker.patch("os.remove")
            mocker.patch("os.path.exists", return_value=True)
            mocker.patch("os.path.getsize", return_value=100)

            # First run
            LogCollectionService.analyze_and_store(date.today())
            assert LogAnalysis.objects.count() == 1

            # Second run
            LogCollectionService.analyze_and_store(date.today())
            assert LogAnalysis.objects.count() == 1  # Should still be 1, not 2
