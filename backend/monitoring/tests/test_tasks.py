import pytest

from monitoring.tasks import cleanup_old_logs_task, daily_log_analysis_task


@pytest.mark.django_db
class TestMonitoringTasks:

    def test_daily_log_analysis_task_orchestration(self, mocker, log_analysis):
        """Test that the orchestrator task coordinates analysis and email sending."""
        # Setup mocks
        mock_analyze = mocker.patch("monitoring.services.LogCollectionService.analyze_and_store")
        mock_email_service = mocker.patch(
            "monitoring.services.LogAnalysisEmailService.generate_and_send"
        )

        # Ensure fixture state
        log_analysis.email_sent = False
        log_analysis.save()

        mock_analyze.return_value = log_analysis

        # Execute task
        result = daily_log_analysis_task()

        # Verify analysis was called
        mock_analyze.assert_called_once()

        # Verify email service was called with correct ID
        mock_email_service.assert_called_once_with(log_analysis.id)

        # Verify email_sent flag was updated in DB
        log_analysis.refresh_from_db()
        assert log_analysis.email_sent is True

        # Verify return value
        assert result["status"] == "success"
        assert result["log_analysis_id"] == log_analysis.id

    def test_cleanup_old_logs_task(self, mocker):
        """Test that the cleanup task calls the service."""
        mock_cleanup = mocker.patch("monitoring.services.LogCollectionService.cleanup_old_logs")
        mock_cleanup.return_value = 5  # 5 records deleted

        # Execute task
        result = cleanup_old_logs_task(days_to_keep=20)

        # Verify
        mock_cleanup.assert_called_once_with(20)
        assert result["status"] == "success"
        assert result["deleted_count"] == 5
