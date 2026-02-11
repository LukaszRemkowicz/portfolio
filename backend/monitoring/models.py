from django.db import models
from django.utils import timezone


class LogAnalysis(models.Model):
    """Stores daily log analysis results from GPT."""

    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    # Metadata
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    analysis_date = models.DateField(db_index=True, unique=True)  # One per day

    # Log collection
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
