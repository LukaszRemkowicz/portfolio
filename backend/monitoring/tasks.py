import logging
from datetime import date

from celery import shared_task

from django.conf import settings

from .services import (
    LogAnalysisEmailService,
    LogAnalysisOrchestrator,
    LogCleanupService,
    MonitoringAgentLogOrchestrator,
    SitemapAnalysisEmailService,
    SitemapAnalysisOrchestrator,
)

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
    retry_backoff=True,
)
def daily_log_analysis_task(self, analysis_date: str | None = None):
    """
    TODO: Legacy orchestrator task for daily log analysis and email notification.

    Flow:
        1. Analyze logs and store results (synchronous)
        2. Generate and send email (asynchronous via LogAnalysisEmailService)
        3. Update email_sent flag

    This task remains as the compatibility boundary while the bounded
    monitoring-agent path is verified in production-like use. It is expected
    to be removed after `daily_monitoring_agent_log_task` is fully trusted and
    becomes the only scheduled implementation.

    Args:
        analysis_date: ISO date string (YYYY-MM-DD), defaults to today
    """
    try:
        if not settings.RUN_LEGACY_DAILY_TASK:
            logger.info(
                "Skipping legacy daily log analysis task because " "RUN_LEGACY_DAILY_TASK=False"
            )
            return {
                "status": "skipped",
                "reason": "legacy_task_disabled",
            }

        if analysis_date:
            date_obj = date.fromisoformat(analysis_date)
        else:
            date_obj = date.today()

        logger.info("Starting daily log analysis for %s", date_obj)

        # Step 1: Analyze and store using orchestrator
        orchestrator = LogAnalysisOrchestrator.create_default()
        log_analysis = orchestrator.analyze_and_store(date_obj)

        # Step 2: Generate and send email (delegates to EmailService)
        email_service = LogAnalysisEmailService(log_analysis)
        email_service.send_email()

        # Step 3: Mark as sent
        log_analysis.mark_email_sent()

        logger.info("Log analysis complete: %s", log_analysis.id)

        return {
            "status": "success",
            "log_analysis_id": log_analysis.id,
            "severity": log_analysis.severity,
            "date": str(log_analysis.analysis_date),
        }

    except Exception as exc:
        logger.exception("Daily log analysis failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(  # type: ignore
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    retry_backoff=True,
)
def daily_monitoring_agent_log_task(self, analysis_date: str | None = None):
    """Run the bounded monitoring-agent log flow and reuse current email delivery.

    This task is the additive Phase 4 entry point for the new monitoring-agent
    execution path. It does not replace `daily_log_analysis_task` yet.
    """
    try:
        if analysis_date:
            date_obj = date.fromisoformat(analysis_date)
        else:
            date_obj = date.today()

        logger.info("Starting monitoring agent log analysis for %s", date_obj)

        orchestrator = MonitoringAgentLogOrchestrator.create_default()
        log_analysis = orchestrator.analyze_and_store(date_obj)

        email_service = LogAnalysisEmailService(log_analysis)
        email_service.send_email()
        log_analysis.mark_email_sent()

        logger.info("Monitoring agent log analysis complete: %s", log_analysis.id)

        return {
            "status": "success",
            "log_analysis_id": log_analysis.id,
            "severity": log_analysis.severity,
            "date": str(log_analysis.analysis_date),
            "runtime": "monitoring_agent",
        }

    except Exception as exc:
        logger.exception("Monitoring agent log analysis failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(  # type: ignore
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    retry_backoff=True,
    track_started=True,
)
def daily_sitemap_analysis_task(self, analysis_date: str | None = None):
    """Run the scheduled sitemap analysis flow and send a separate sitemap email."""
    try:
        if analysis_date:
            date_obj = date.fromisoformat(analysis_date)
        else:
            date_obj = date.today()

        logger.info("Starting sitemap analysis for %s", date_obj)

        orchestrator = SitemapAnalysisOrchestrator.create_default()
        sitemap_analysis = orchestrator.analyze_and_store(date_obj)

        email_service = SitemapAnalysisEmailService(sitemap_analysis)
        email_service.send_email()
        sitemap_analysis.mark_email_sent()

        logger.info("Sitemap analysis complete: %s", sitemap_analysis.id)

        return {
            "status": "success",
            "sitemap_analysis_id": sitemap_analysis.id,
            "severity": sitemap_analysis.severity,
            "date": str(sitemap_analysis.analysis_date),
        }

    except Exception as exc:
        logger.exception("Sitemap analysis failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(  # type: ignore
    bind=True,
    max_retries=1,
)
def cleanup_old_logs_task(self, days_to_keep: int = 30):
    """
    Celery task to clean up old log analysis records.

    Args:
        days_to_keep: Number of days to retain (default: 30)
    """
    try:
        logger.info("Starting log cleanup (keeping last %d days)", days_to_keep)

        deleted_count = LogCleanupService.cleanup_old_logs(days_to_keep)

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
        }

    except Exception as exc:
        logger.exception("Log cleanup failed: %s", exc)
        raise self.retry(exc=exc)
