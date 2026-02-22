import pytest

from monitoring.tasks import cleanup_old_logs_task, daily_log_analysis_task


@pytest.mark.django_db
class TestMonitoringTasks:

    def test_daily_log_analysis_task_orchestration(self, mocker, log_analysis):
        """Test that the orchestrator task coordinates analysis and email sending."""
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
