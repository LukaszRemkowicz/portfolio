# backend/monitoring/services.py
import logging
import os
import time
from datetime import date, datetime, timezone
from typing import Optional

from django.conf import settings
from django.core.files import File

from common.llm.registry import LLMProviderRegistry
from common.services import BaseEmailService

from .agents import LogAnalysisAgent
from .models import LogAnalysis

logger = logging.getLogger(__name__)


class DockerLogCollector:
    """Reads pre-collected logs from a volume-mounted directory.

    Logs are collected daily by `scripts/monitoring/collect-logs.sh` (host cron job)
    and written to DOCKER_LOGS_DIR, which is mounted read-only into this container.
    """

    MAX_STALENESS_HOURS = 25

    @classmethod
    def _check_staleness(cls, logs_dir: str) -> None:
        """Warn if collected_at.txt indicates logs older than MAX_STALENESS_HOURS."""
        collected_at_path = os.path.join(logs_dir, "collected_at.txt")
        if not os.path.exists(collected_at_path):
            logger.warning(
                "collected_at.txt not found in %s — cron job may not have run yet",
                logs_dir,
            )
            return
        with open(collected_at_path) as f:
            collected_at_raw = f.read().strip()
        collected_at = datetime.fromisoformat(collected_at_raw).replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - collected_at).total_seconds() / 3600
        if age_hours > cls.MAX_STALENESS_HOURS:
            logger.warning(
                "Docker logs are %.1f hours old (expected <%d h) — cron job may have missed a run",
                age_hours,
                cls.MAX_STALENESS_HOURS,
            )

    @classmethod
    def get_collected_at(cls) -> str:
        """Return the raw ISO timestamp from collected_at.txt, or empty string if missing."""
        path = os.path.join(settings.DOCKER_LOGS_DIR, "collected_at.txt")
        if os.path.exists(path):
            with open(path) as f:
                return f.read().strip()
        return ""

    @classmethod
    def collect_logs(cls) -> tuple[str, str, Optional[str]]:
        """Return paths to pre-collected log files from the mounted volume.

        Returns:
            Tuple of (backend_log_path, frontend_log_path, nginx_log_path|None)
            nginx_log_path is None if nginx.log was not collected (warns, doesn't fail).

        Raises:
            FileNotFoundError: If backend or frontend log files are missing (cron hasn't run)
        """
        logs_dir: str = settings.DOCKER_LOGS_DIR

        backend_log_path = os.path.join(logs_dir, "backend.log")
        frontend_log_path = os.path.join(logs_dir, "frontend.log")
        nginx_log_path = os.path.join(logs_dir, "nginx.log")

        for path in (backend_log_path, frontend_log_path):
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"Log file not found: {path}. "
                    "Ensure the collect-logs.sh cron job has run successfully."
                )

        cls._check_staleness(logs_dir)

        nginx_path: Optional[str] = None
        if os.path.exists(nginx_log_path):
            nginx_path = nginx_log_path
            nginx_size = os.path.getsize(nginx_log_path)
        else:
            logger.warning(
                "nginx.log not found in %s — nginx logs will be skipped. "
                "Ensure NGINX_LOG_DIR is set in collect-logs.sh.",
                logs_dir,
            )
            nginx_size = 0

        be_size = os.path.getsize(backend_log_path)
        fe_size = os.path.getsize(frontend_log_path)
        logger.info(
            "Read logs: backend=%d bytes, frontend=%d bytes, nginx=%d bytes",
            be_size,
            fe_size,
            nginx_size,
        )

        return backend_log_path, frontend_log_path, nginx_path


class LogAnalyzer:
    """Analyzes logs using LLM agent."""

    def __init__(self, agent: LogAnalysisAgent):
        self.agent = agent

    def analyze_logs_from_files(
        self,
        backend_log_path: str,
        frontend_log_path: str,
        nginx_log_path: Optional[str] = None,
        collected_at: str = "",
        historical_context: str = "",
    ) -> dict:
        """
        Analyze logs using LLM.

        Args:
            backend_log_path: Path to backend log file
            frontend_log_path: Path to frontend log file
            nginx_log_path: Optional path to nginx log file
            collected_at: ISO timestamp string from collected_at.txt
            historical_context: Pre-formatted string from HistoricalContextBuilder

        Returns:
            Analysis result dict with keys: summary, severity, key_findings,
            recommendations, trend_summary, gpt_tokens_used

        Raises:
            ValueError: If analysis returns empty result
        """
        result = self.agent.analyze_logs_from_files(
            backend_log_path,
            frontend_log_path,
            nginx_log_path,
            collected_at,
            historical_context=historical_context,
        )

        if not result:
            raise ValueError("LLM analysis returned empty result")

        # Ensure findings is a list
        findings = result.get("key_findings", [])
        if isinstance(findings, str):
            result["key_findings"] = [findings]

        return result


class LogStorageService:
    """Stores log analysis results in database."""

    @classmethod
    def create_or_replace_analysis(cls, analysis_date: date, **kwargs) -> LogAnalysis:
        """
        Idempotent creation of LogAnalysis record.

        Deletes any existing record for the same date before creating new one.

        Args:
            analysis_date: Date for the analysis
            **kwargs: Fields to pass to LogAnalysis.objects.create()

        Returns:
            LogAnalysis: Created instance
        """
        existing_count = LogAnalysis.objects.for_date(analysis_date).count()
        if existing_count > 0:
            logger.info(
                "Replacing %d existing analysis record(s) for %s", existing_count, analysis_date
            )
            LogAnalysis.objects.for_date(analysis_date).delete()
        return LogAnalysis.objects.create(analysis_date=analysis_date, **kwargs)

    @classmethod
    def attach_log_files(
        cls,
        log_analysis: LogAnalysis,
        backend_path: str,
        frontend_path: str,
        analysis_date: date,
        nginx_path: Optional[str] = None,
    ) -> None:
        """
        Attach log files to the analysis record.

        Args:
            log_analysis: LogAnalysis instance to attach files to
            backend_path: Path to backend log file
            frontend_path: Path to frontend log file
            analysis_date: Date for filename generation
            nginx_path: Optional path to nginx combined log file
        """
        with open(backend_path, "rb") as f:
            log_analysis.backend_logs.save(f"backend_{analysis_date}.log", File(f))

        with open(frontend_path, "rb") as f:
            log_analysis.frontend_logs.save(f"frontend_{analysis_date}.log", File(f))

        if nginx_path and os.path.exists(nginx_path):
            with open(nginx_path, "rb") as f:
                log_analysis.nginx_logs.save(f"nginx_{analysis_date}.log", File(f))


class LogCleanupService:
    """Cleans up old log analysis records."""

    @classmethod
    def cleanup_old_logs(cls, days_to_keep: int = 30) -> int:
        """
        Delete log analysis records older than specified days.

        Args:
            days_to_keep: Number of days to retain (default: 30)

        Returns:
            Number of records deleted
        """
        deleted_count, _ = LogAnalysis.objects.older_than(days_to_keep).delete()

        logger.info(
            "Cleaned up %d log analysis records older than %d days", deleted_count, days_to_keep
        )

        return deleted_count


class HistoricalContextBuilder:
    """
    Formats LogAnalysis DB records into a prompt-ready markdown block for LLM context.

    Responsibility: serialise raw queryset data into the text the LLM can understand.
    Data access is delegated to LogAnalysis.objects.last_5_days().
    """

    @classmethod
    def build(cls, exclude_date: date | None = None) -> str:
        """Return formatted markdown block of last-5-day analyses, or '' if none exist."""
        records = LogAnalysis.objects.last_5_days(exclude_date=exclude_date)
        if not records.exists():
            return ""
        lines = []
        for record in records:
            lines.append(
                f"## {record.analysis_date} \u2014 Severity: {record.severity}\n"
                f"Summary: {record.summary}\n"
                f"Key findings: {record.key_findings}\n"
                f"Recommendations: {record.recommendations}"
            )
        return "\n\n".join(lines)


class LogAnalysisOrchestrator:
    """Orchestrates the log analysis workflow."""

    def __init__(
        self,
        collector: DockerLogCollector,
        analyzer: LogAnalyzer,
        storage: LogStorageService,
    ):
        self.collector = collector
        self.analyzer = analyzer
        self.storage = storage

    def analyze_and_store(self, analysis_date: Optional[date] = None) -> LogAnalysis:
        """
        Main workflow: collect logs, analyze, and store results.

        Args:
            analysis_date: Date for analysis (defaults to today)

        Returns:
            LogAnalysis instance

        Raises:
            Various exceptions from collector, analyzer, or storage
        """
        if analysis_date is None:
            analysis_date = date.today()

        start_time = time.time()
        backend_log_path = None
        frontend_log_path = None
        nginx_log_path = None

        try:
            backend_log_path, frontend_log_path, nginx_log_path, log_size = self._collect_logs()
            historical_context = self._build_historical_context(analysis_date)
            analysis_result = self._run_analysis(
                backend_log_path, frontend_log_path, nginx_log_path, historical_context
            )
            log_analysis = self._store_results(
                analysis_date,
                log_size,
                analysis_result,
                start_time,
                backend_log_path,
                frontend_log_path,
                nginx_log_path,
            )
            logger.info(
                "Log analysis complete for %s: record_id=%s, severity=%s",
                analysis_date,
                log_analysis.id,
                log_analysis.severity,
            )
            return log_analysis

        except Exception as error:
            logger.exception("Log analysis failed for date %s", analysis_date)
            self._store_error(
                analysis_date,
                error,
                start_time,
                backend_log_path,
                frontend_log_path,
                nginx_log_path,
            )
            raise

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _collect_logs(self) -> tuple[str, str, Optional[str], int]:
        """Collect log files and return (backend_path, frontend_path, nginx_path, total_bytes)."""
        backend_path, frontend_path, nginx_path = self.collector.collect_logs()
        log_size = (
            os.path.getsize(backend_path)
            + os.path.getsize(frontend_path)
            + (os.path.getsize(nginx_path) if nginx_path else 0)
        )
        if log_size == 0:
            logger.warning("No logs collected from Docker containers")
        return backend_path, frontend_path, nginx_path, log_size

    def _build_historical_context(self, analysis_date: date) -> str:
        """Fetch and format prior DB analyses into an LLM-ready context string."""
        historical_context = HistoricalContextBuilder.build(exclude_date=analysis_date)
        if historical_context:
            logger.info("Historical context loaded (%d chars)", len(historical_context))
        else:
            logger.info("No historical context available (first run or all records older than 5d)")
        return historical_context

    def _run_analysis(
        self,
        backend_path: str,
        frontend_path: str,
        nginx_path: Optional[str],
        historical_context: str,
    ) -> dict:
        """Run LLM analysis and return the result dict."""
        collected_at = self.collector.get_collected_at()
        return self.analyzer.analyze_logs_from_files(
            backend_path,
            frontend_path,
            nginx_path,
            collected_at,
            historical_context=historical_context,
        )

    def _store_results(
        self,
        analysis_date: date,
        log_size: int,
        analysis_result: dict,
        start_time: float,
        backend_path: str,
        frontend_path: str,
        nginx_path: Optional[str],
    ) -> LogAnalysis:
        """Persist analysis results and attach log files."""
        log_analysis = self.storage.create_or_replace_analysis(
            analysis_date=analysis_date,
            log_size_bytes=log_size,
            summary=analysis_result.get("summary", "No summary provided"),
            severity=analysis_result.get("severity", "INFO"),
            key_findings=analysis_result.get("key_findings", []),
            recommendations=analysis_result.get("recommendations", ""),
            trend_summary=analysis_result.get("trend_summary", ""),
            execution_time_seconds=time.time() - start_time,
            gpt_tokens_used=analysis_result.get("gpt_tokens_used", 0),
            gpt_cost_usd=analysis_result.get("gpt_cost_usd", 0.0),
        )
        self.storage.attach_log_files(
            log_analysis, backend_path, frontend_path, analysis_date, nginx_path
        )
        return log_analysis

    def _store_error(
        self,
        analysis_date: date,
        error: Exception,
        start_time: float,
        backend_path: Optional[str] = None,
        frontend_path: Optional[str] = None,
        nginx_path: Optional[str] = None,
    ) -> None:
        """Persist a CRITICAL error record so the failure is visible in the admin."""
        log_analysis = self.storage.create_or_replace_analysis(
            analysis_date=analysis_date,
            backend_logs=None,
            frontend_logs=None,
            error_message=str(error),
            execution_time_seconds=time.time() - start_time,
            severity=LogAnalysis.Severity.CRITICAL,
            summary=f"Analysis Failed: {str(error)}",
        )
        if (
            backend_path
            and frontend_path
            and os.path.exists(backend_path)
            and os.path.exists(frontend_path)
        ):
            self.storage.attach_log_files(
                log_analysis, backend_path, frontend_path, analysis_date, nginx_path
            )

    @classmethod
    def create_default(cls) -> "LogAnalysisOrchestrator":
        """Factory method to create orchestrator with default dependencies."""

        # Fail-fast: No defaults, settings must be explicit
        provider_name = settings.MONITORING_LLM_PROVIDER
        provider = LLMProviderRegistry.get(provider_name)
        agent = LogAnalysisAgent(provider)

        return cls(
            collector=DockerLogCollector(),
            analyzer=LogAnalyzer(agent),
            storage=LogStorageService(),
        )


class LogAnalysisEmailService(BaseEmailService):
    """
    Handles LogAnalysis-specific email generation and sending.

    This service encapsulates all business logic related to LogAnalysis emails,
    including data fetching, context preparation, and template rendering.
    """

    def __init__(self, log_analysis: LogAnalysis):
        """
        Initialize with log analysis instance.

        Args:
            log_analysis: LogAnalysis instance to send email for
        """
        self.log_analysis = log_analysis

    def get_subject(self) -> str:
        """Generate email subject line."""
        return self.log_analysis.get_email_subject()

    def get_context(self) -> dict:
        """Generate template context dictionary."""
        return self.log_analysis.get_email_context()

    def get_template_name(self) -> str:
        """Return path to email template."""
        return "monitoring/email/log_analysis.html"
