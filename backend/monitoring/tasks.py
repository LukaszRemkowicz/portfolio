import logging
from datetime import date

from celery import shared_task

from .services import LogCollectionService

logger = logging.getLogger(__name__)


@shared_task(  # type: ignore
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
    retry_backoff=True,
)
def daily_log_analysis_task(self, analysis_date: str | None = None):
    """
    Celery task for daily log analysis.

    Args:
        analysis_date: ISO date string (YYYY-MM-DD), defaults to today
    """
    try:
        if analysis_date:
            date_obj = date.fromisoformat(analysis_date)
        else:
            date_obj = date.today()

        logger.info(f"Starting daily log analysis for {date_obj}")

        log_analysis = LogCollectionService.analyze_and_store(date_obj)

        return {
            "status": "success",
            "log_analysis_id": log_analysis.id,
            "severity": log_analysis.severity,
            "date": str(log_analysis.analysis_date),
        }

    except Exception as exc:
        logger.exception(f"Daily log analysis failed: {exc}")
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
        logger.info(f"Starting log cleanup (keeping last {days_to_keep} days)")

        deleted_count = LogCollectionService.cleanup_old_logs(days_to_keep)

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
        }

    except Exception as exc:
        logger.exception(f"Log cleanup failed: {exc}")
        raise self.retry(exc=exc)
