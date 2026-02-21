from datetime import date

import pytest

from django.template.loader import render_to_string

from monitoring.services import LogAnalysisEmailService


@pytest.mark.django_db
class TestEmailNotifications:

    def test_email_rendering_context_and_content(self, log_analysis):
        """
        Verify that the HTML template renders correctly with:
        1. Context data (summary, findings, metrics).
        2. Responsive CSS classes (wrapper, container-bg).
        3. Dynamic links (admin_domain).
        """
        context = {
            "environment": "testing",
            "log_analysis": log_analysis,
            "log_size_kb": f"{log_analysis.log_size_bytes / 1024:.1f}",
            "execution_time": f"{log_analysis.execution_time_seconds:.1f}",
            "admin_domain": "admin.example.com",
        }

        html_content = render_to_string("monitoring/email/log_analysis.html", context)

        # Check basic content
        assert "Daily Log Analysis" in html_content
        assert "System is healthy." in html_content
        assert "Database latency normal" in html_content
        assert "Monitor disk usage." in html_content
        assert "admin.example.com" in html_content
        assert "TESTING" in html_content  # Environment upper-cased

        # Check Responsive / Theme Classes
        assert "wrapper" in html_content
        assert "container-bg" in html_content
        assert "text-main" in html_content

        # Check specific style overrides (presence of dark mode media query)
        assert "@media (prefers-color-scheme: dark)" in html_content
        assert "u+.body" in html_content  # Gmail hack presence

    def test_generate_email_content_via_model(self, log_analysis):
        """Test that model methods generate correct subject and context."""
        # Use model methods directly
        subject = log_analysis.get_email_subject()
        context = log_analysis.get_email_context()

        # Verify subject
        assert subject == f"[INFO] Daily Log Analysis - {date.today()}"

        # Verify context
        assert context["log_analysis"] == log_analysis
        assert "environment" in context
        assert "log_size_kb" in context
        assert "execution_time" in context

        # Render template with context
        html_content = render_to_string("monitoring/email/log_analysis.html", context)

        # Verify body contains key info
        assert "System is healthy." in html_content
        assert "Database latency normal" in html_content
        assert "Monitor disk usage." in html_content

    def test_log_analysis_email_service_integration(self, mocker, log_analysis):
        """Test that LogAnalysisEmailService generates and sends email correctly."""
        mock_send_async = mocker.patch("common.services.EmailService.send_async")

        LogAnalysisEmailService(log_analysis).send_email()

        # Verify send_async was called
        mock_send_async.assert_called_once()

        # Verify arguments
        call_args = mock_send_async.call_args
        subject = call_args[0][0]
        html_content = call_args[0][1]

        assert "[INFO] Daily Log Analysis" in subject
        assert "System is healthy." in html_content
