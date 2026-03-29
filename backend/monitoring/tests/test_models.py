# backend/monitoring/tests/test_models.py
"""Tests for LogAnalysis model methods, properties, and custom manager."""

from datetime import date, timedelta

import pytest

from django.conf import settings

from monitoring.models import LogAnalysis, SitemapAnalysis
from monitoring.tests.factories import LogAnalysisFactory, SitemapAnalysisFactory


@pytest.mark.django_db
class TestLogAnalysisQuerySet:
    """Test custom queryset methods."""

    def test_for_date_filters_correctly(self):
        """Verify for_date() filters by specific date."""
        target_date = date(2024, 1, 15)
        LogAnalysisFactory(analysis_date=target_date)
        LogAnalysisFactory(analysis_date=date(2024, 1, 16))

        results = LogAnalysis.objects.for_date(target_date)
        assert results.count() == 1
        assert results.first().analysis_date == target_date

    def test_older_than_filters_correctly(self):
        """Verify older_than() filters by age in days."""
        old_date = date.today() - timedelta(days=35)
        recent_date = date.today() - timedelta(days=5)

        LogAnalysisFactory(analysis_date=old_date)
        LogAnalysisFactory(analysis_date=recent_date)

        results = LogAnalysis.objects.older_than(30)
        assert results.count() == 1
        assert results.first().analysis_date == old_date

    def test_older_than_boundary_case(self):
        """Verify older_than() excludes exact boundary date."""
        boundary_date = date.today() - timedelta(days=30)
        LogAnalysisFactory(analysis_date=boundary_date)

        results = LogAnalysis.objects.older_than(30)
        # Should NOT include the boundary date (uses __lt, not __lte)
        assert results.count() == 0

    def test_unsent_emails_filters_correctly(self):
        """Verify unsent_emails() filters by email_sent=False."""
        LogAnalysisFactory(analysis_date=date(2024, 3, 1), email_sent=True)
        LogAnalysisFactory(analysis_date=date(2024, 3, 2), email_sent=False)

        results = LogAnalysis.objects.unsent_emails()
        assert results.count() == 1
        assert results.first().email_sent is False

    def test_by_severity_filters_correctly(self):
        """Verify by_severity() filters by severity level."""
        LogAnalysisFactory(analysis_date=date(2024, 4, 1), severity=LogAnalysis.Severity.WARNING)
        LogAnalysisFactory(analysis_date=date(2024, 4, 2), severity=LogAnalysis.Severity.INFO)

        results = LogAnalysis.objects.by_severity(LogAnalysis.Severity.WARNING)
        assert results.count() == 1
        assert results.first().severity == LogAnalysis.Severity.WARNING

    def test_critical_filters_by_severity(self):
        """Verify critical() is shorthand for by_severity(CRITICAL)."""
        LogAnalysisFactory(analysis_date=date(2024, 5, 1), severity=LogAnalysis.Severity.CRITICAL)
        LogAnalysisFactory(analysis_date=date(2024, 5, 2), severity=LogAnalysis.Severity.INFO)

        results = LogAnalysis.objects.critical()
        assert results.count() == 1
        assert results.first().severity == LogAnalysis.Severity.CRITICAL

    def test_queryset_methods_are_chainable(self):
        """Verify queryset methods can be chained."""
        old_critical = LogAnalysisFactory(
            analysis_date=date.today() - timedelta(days=35),
            severity=LogAnalysis.Severity.CRITICAL,
            email_sent=False,
        )
        LogAnalysisFactory(
            analysis_date=date.today() - timedelta(days=5),
            severity=LogAnalysis.Severity.CRITICAL,
        )
        LogAnalysisFactory(
            analysis_date=date.today() - timedelta(days=40),
            severity=LogAnalysis.Severity.INFO,
        )

        # Chain: older than 30 days AND critical AND unsent
        results = LogAnalysis.objects.older_than(30).critical().unsent_emails()
        assert results.count() == 1
        assert results.first().id == old_critical.id


@pytest.mark.django_db
class TestLogAnalysisProperties:
    """Test model properties."""

    def test_log_size_kb_formats_correctly(self):
        """Verify log_size_kb property formats bytes to KB with 1 decimal."""
        log = LogAnalysisFactory(log_size_bytes=2048)
        assert log.log_size_kb == "2.0"

    def test_log_size_kb_rounds_correctly(self):
        """Verify log_size_kb rounds to 1 decimal place."""
        log = LogAnalysisFactory(log_size_bytes=1536)  # 1.5 KB
        assert log.log_size_kb == "1.5"

    def test_log_size_kb_handles_zero(self):
        """Verify log_size_kb handles zero bytes."""
        log = LogAnalysisFactory(log_size_bytes=0)
        assert log.log_size_kb == "0.0"

    def test_execution_time_formatted(self):
        """Verify execution_time_formatted property formats seconds with 1 decimal."""
        log = LogAnalysisFactory(execution_time_seconds=3.14159)
        assert log.execution_time_formatted == "3.1"

    def test_execution_time_formatted_rounds_correctly(self):
        """Verify execution_time_formatted rounds to 1 decimal place."""
        log = LogAnalysisFactory(execution_time_seconds=5.56)
        assert log.execution_time_formatted == "5.6"


@pytest.mark.django_db
class TestLogAnalysisMethods:
    """Test model methods."""

    def test_get_email_subject_format(self):
        """Verify get_email_subject() returns correct format."""
        log = LogAnalysisFactory(
            severity=LogAnalysis.Severity.WARNING, analysis_date=date(2024, 1, 15)
        )
        subject = log.get_email_subject()
        assert (
            subject == f"[{settings.ENVIRONMENT.upper()}][WARNING] Daily Log Analysis - 2024-01-15"
        )

    def test_get_email_subject_with_critical_severity(self):
        """Verify get_email_subject() works with CRITICAL severity."""
        log = LogAnalysisFactory(
            severity=LogAnalysis.Severity.CRITICAL, analysis_date=date(2024, 2, 20)
        )
        subject = log.get_email_subject()
        assert (
            subject == f"[{settings.ENVIRONMENT.upper()}][CRITICAL] Daily Log Analysis - 2024-02-20"
        )

    def test_get_email_context_contains_required_keys(self):
        """Verify get_email_context() returns all required keys."""
        log = LogAnalysisFactory()
        context = log.get_email_context()

        assert "environment" in context
        assert "log_analysis" in context
        assert "log_size_kb" in context
        assert "execution_time" in context
        assert "admin_domain" in context

    def test_get_email_context_values(self):
        """Verify get_email_context() returns correct values."""
        log = LogAnalysisFactory(log_size_bytes=2048, execution_time_seconds=3.14)
        context = log.get_email_context()

        assert context["environment"] == settings.ENVIRONMENT
        assert context["log_analysis"] == log
        assert context["log_size_kb"] == "2.0"
        assert context["execution_time"] == "3.1"
        assert context["admin_domain"] == settings.ADMIN_DOMAIN

    def test_mark_email_sent_updates_field(self):
        """Verify mark_email_sent() sets email_sent to True."""
        log = LogAnalysisFactory(email_sent=False)
        log.mark_email_sent()

        log.refresh_from_db()
        assert log.email_sent is True

    def test_mark_email_sent_is_idempotent(self):
        """Verify mark_email_sent() can be called multiple times safely."""
        log = LogAnalysisFactory(email_sent=False)
        log.mark_email_sent()
        log.mark_email_sent()  # Call again

        log.refresh_from_db()
        assert log.email_sent is True

    def test_mark_email_sent_only_updates_email_sent_field(self):
        """Verify mark_email_sent() uses update_fields to only update email_sent."""
        log = LogAnalysisFactory(email_sent=False, summary="Original")

        # Modify summary in memory but don't save
        log.summary = "Modified"
        log.mark_email_sent()

        log.refresh_from_db()
        # email_sent should be updated, but summary should remain original
        assert log.email_sent is True
        assert log.summary == "Original"


@pytest.mark.django_db
class TestLogAnalysisManager:
    """Test last_5_days queryset/manager method and historical context."""

    def test_last_5_days_returns_records_within_window(self):
        """Records within last 5 days are returned; older ones are not."""
        inside = LogAnalysisFactory(analysis_date=date.today() - timedelta(days=3))
        LogAnalysisFactory(analysis_date=date.today() - timedelta(days=6))

        results = LogAnalysis.objects.last_5_days()
        assert inside in results
        assert results.count() == 1

    def test_last_5_days_boundary_is_inclusive(self):
        """A record exactly 5 days old is included (analysis_date__gte)."""
        boundary = LogAnalysisFactory(analysis_date=date.today() - timedelta(days=5))

        results = LogAnalysis.objects.last_5_days()
        assert boundary in results

    def test_last_5_days_ordered_newest_first(self):
        """Records are ordered by analysis_date descending."""
        older = LogAnalysisFactory(analysis_date=date.today() - timedelta(days=4))
        newer = LogAnalysisFactory(analysis_date=date.today() - timedelta(days=1))

        results = list(LogAnalysis.objects.last_5_days())
        assert results[0] == newer
        assert results[1] == older

    def test_last_5_days_excludes_given_date(self):
        """exclude_date param omits the matching record."""
        today_record = LogAnalysisFactory(analysis_date=date.today())
        yesterday = LogAnalysisFactory(analysis_date=date.today() - timedelta(days=1))

        results = LogAnalysis.objects.last_5_days(exclude_date=date.today())
        assert today_record not in results
        assert yesterday in results

    def test_last_5_days_empty_db_returns_empty_qs(self):
        """No records in DB returns empty queryset."""
        assert LogAnalysis.objects.last_5_days().count() == 0

    def test_trend_summary_field_exists_and_blank_by_default(self):
        """trend_summary field exists and defaults to blank string."""
        log = LogAnalysisFactory()
        assert hasattr(log, "trend_summary")
        assert log.trend_summary == ""


@pytest.mark.django_db
class TestSitemapAnalysisMethods:
    def test_get_email_subject_format(self):
        sitemap_analysis = SitemapAnalysisFactory(
            severity=SitemapAnalysis.Severity.WARNING,
            analysis_date=date(2024, 3, 10),
        )

        subject = sitemap_analysis.get_email_subject()

        assert subject == f"[{settings.ENVIRONMENT.upper()}][WARNING] Sitemap Analysis - 2024-03-10"

    def test_get_email_context_contains_required_keys(self):
        sitemap_analysis = SitemapAnalysisFactory(execution_time_seconds=8.6)

        context = sitemap_analysis.get_email_context()

        assert context["environment"] == settings.ENVIRONMENT
        assert context["sitemap_analysis"] == sitemap_analysis
        assert context["execution_time"] == "8.6"
        assert context["admin_domain"] == settings.ADMIN_DOMAIN

    def test_mark_email_sent_updates_field(self):
        sitemap_analysis = SitemapAnalysisFactory(email_sent=False)

        sitemap_analysis.mark_email_sent()
        sitemap_analysis.refresh_from_db()

        assert sitemap_analysis.email_sent is True
