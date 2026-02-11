from datetime import date
from unittest.mock import mock_open, patch

import pytest

from monitoring.models import LogAnalysis
from monitoring.services import LogCollectionService


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    with patch("monitoring.services.logger") as mock:
        yield mock


@pytest.mark.django_db
class TestLogCollectionService:
    def test_get_docker_logs_success(self, mock_subprocess):
        """Test successful docker log retrieval."""
        mock_subprocess.return_value.stdout = "Log content"
        mock_subprocess.return_value.returncode = 0

        # Must mock shutil.which and open/writing
        with (
            patch("shutil.which", return_value="/usr/bin/docker"),
            patch("builtins.open", mock_open()),
            patch("os.path.getsize", return_value=100),
        ):

            logs = LogCollectionService.collect_docker_logs()

            assert len(logs) == 2
            assert "backend" in logs[0]
            assert "frontend" in logs[1]
            assert "logs" in mock_subprocess.call_args[0][0]
            assert "--tail=2000" in mock_subprocess.call_args[0][0]

    def test_cleanup_old_logs(self):
        """Test that old logs are deleted."""
        # Create some old and new logs
        old_log = LogAnalysis.objects.create(
            analysis_date=date(2020, 1, 1), summary="Old", severity="INFO"
        )
        new_log = LogAnalysis.objects.create(
            analysis_date=date.today(), summary="New", severity="INFO"
        )

        # Override today for the test logic if needed, or just rely on date math
        # simplistic: delete anything older than 365 days
        LogCollectionService.cleanup_old_logs(days_to_keep=30)

        assert LogAnalysis.objects.filter(pk=new_log.pk).exists()
        # The old log is definitely older than 30 days from now
        assert not LogAnalysis.objects.filter(pk=old_log.pk).exists()

    @patch("monitoring.services.LogCollectionService.collect_docker_logs")
    @patch("monitoring.services.LogCollectionService.agent")
    def test_analyze_and_store_creates_record(self, mock_agent, mock_get_logs):
        """Test the full analysis flow creates a record."""
        mock_get_logs.return_value = ("/tmp/backend.log", "/tmp/frontend.log")

        # Mock agent response
        mock_agent.analyze_logs_from_files.return_value = {
            "summary": "Analysis Summary",
            "severity": "WARNING",
            "key_findings": ["Finding 1"],
            "recommendations": "Fix it",
            "gpt_tokens_used": 150,
        }

        # Mock file operations to prevent reading/writing real files in /tmp
        # We need to mock os.path.exists and os.path.getsize too since they are called
        with (
            patch("builtins.open", mock_open(read_data="Mock logs")),
            patch("os.remove"),
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=100),
        ):
            record = LogCollectionService.analyze_and_store(analysis_date=date.today())

        assert record is not None
        assert record.summary == "Analysis Summary"
        assert record.severity == "WARNING"
        assert record.gpt_tokens_used == 150
        assert LogAnalysis.objects.count() == 1

    @patch("monitoring.services.LogCollectionService.collect_docker_logs")
    @patch("monitoring.services.LogCollectionService.agent")
    def test_analyze_and_store_idempotency(self, mock_agent, mock_get_logs):
        """Test that re-running analysis for same day replaces the record."""
        mock_get_logs.return_value = ("/tmp/backend.log", "/tmp/frontend.log")
        mock_agent.analyze_logs_from_files.return_value = {
            "summary": "Summary",
            "severity": "INFO",
            "gpt_tokens_used": 100,
        }

        with (
            patch("builtins.open", mock_open(read_data="Mock logs")),
            patch("os.remove"),
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=100),
        ):
            # First run
            LogCollectionService.analyze_and_store(date.today())
            assert LogAnalysis.objects.count() == 1

            # Second run
            LogCollectionService.analyze_and_store(date.today())
            assert LogAnalysis.objects.count() == 1  # Should still be 1, not 2
