import logging
from datetime import date

from celery import shared_task

from .services import LogAnalysisEmailService, LogAnalysisOrchestrator, LogCleanupService

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
    retry_backoff=True,
)
def daily_log_analysis_task(self, analysis_date: str | None = None):
    """
    Orchestrator task for daily log analysis and email notification.

    Flow:
        1. Analyze logs and store results (synchronous)
        2. Generate and send email (asynchronous via LogAnalysisEmailService)
        3. Update email_sent flag

    Args:
        analysis_date: ISO date string (YYYY-MM-DD), defaults to today
    """
    try:
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
