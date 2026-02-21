from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class LogAnalysisQuerySet(models.QuerySet):
    """Custom queryset for LogAnalysis with business logic."""

    def for_date(self, analysis_date: date) -> "LogAnalysisQuerySet":
        """Filter logs for a specific date."""
        return self.filter(analysis_date=analysis_date)

    def older_than(self, days: int) -> "LogAnalysisQuerySet":
        """Filter logs older than N days."""
        cutoff = date.today() - timedelta(days=days)
        return self.filter(analysis_date__lt=cutoff)

    def unsent_emails(self) -> "LogAnalysisQuerySet":
        """Filter logs where email hasn't been sent."""
        return self.filter(email_sent=False)

    def by_severity(self, severity: str) -> "LogAnalysisQuerySet":
        """Filter by severity level."""
        return self.filter(severity=severity)

    def critical(self) -> "LogAnalysisQuerySet":
        """Filter critical severity logs."""
        return self.by_severity(LogAnalysis.Severity.CRITICAL)


class LogAnalysisManager(models.Manager):
    """Custom manager for LogAnalysis."""

    def get_queryset(self) -> LogAnalysisQuerySet:
        return LogAnalysisQuerySet(self.model, using=self._db)

    def for_date(self, analysis_date: date) -> LogAnalysisQuerySet:
        return self.get_queryset().for_date(analysis_date)

    def older_than(self, days: int) -> LogAnalysisQuerySet:
        return self.get_queryset().older_than(days)

    def unsent_emails(self) -> LogAnalysisQuerySet:
        return self.get_queryset().unsent_emails()

    def by_severity(self, severity: str) -> LogAnalysisQuerySet:
        return self.get_queryset().by_severity(severity)

    def critical(self) -> LogAnalysisQuerySet:
        return self.get_queryset().critical()


class LogAnalysis(models.Model):
    """Stores daily log analysis results from GPT."""

    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    # Custom manager
    objects = LogAnalysisManager()

    # Metadata
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    analysis_date = models.DateField(db_index=True, unique=True)  # One per day

    # Log collection
    backend_logs = models.FileField(
        upload_to="logs/%Y/%m/%d/", help_text="Raw backend logs", null=True, blank=True
    )
    frontend_logs = models.FileField(
        upload_to="logs/%Y/%m/%d/", help_text="Raw frontend logs", null=True, blank=True
    )
    log_size_bytes = models.IntegerField(default=0)

    # GPT Analysis
    summary = models.TextField(help_text="GPT-generated summary")
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO)
    key_findings = models.JSONField(default=list, help_text="List of important findings")
    recommendations = models.TextField(blank=True, help_text="GPT recommendations")

    # Execution tracking
    execution_time_seconds = models.FloatField(default=0.0)
    gpt_tokens_used = models.IntegerField(default=0)
    email_sent = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-analysis_date"]
        verbose_name = "Log Analysis"
        verbose_name_plural = "Log Analyses"

    def __str__(self):
        return f"Log Analysis {self.analysis_date} ({self.severity})"

    # Properties for formatting (read-only computed values)
    @property
    def log_size_kb(self) -> str:
        """Format log size in KB."""
        return f"{self.log_size_bytes / 1024:.1f}"

    @property
    def execution_time_formatted(self) -> str:
        """Format execution time in seconds."""
        return f"{self.execution_time_seconds:.1f}"

    # Domain logic methods
    def get_email_subject(self) -> str:
        """Generate email subject for this analysis."""
        return f"[{self.severity}] Daily Log Analysis - {self.analysis_date}"

    def get_email_context(self) -> dict:
        """Generate template context for email rendering."""
        return {
            "environment": settings.ENVIRONMENT,
            "log_analysis": self,
            "log_size_kb": self.log_size_kb,
            "execution_time": self.execution_time_formatted,
            "admin_domain": settings.ADMIN_DOMAIN,
        }

    def mark_email_sent(self) -> None:
        """Mark email as sent (state transition)."""
        self.email_sent = True
        self.save(update_fields=["email_sent"])
