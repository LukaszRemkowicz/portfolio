# backend/monitoring/services.py
import logging
import os
import time
from collections.abc import Mapping
from datetime import date, datetime, timezone
from typing import Optional

from django.conf import settings
from django.core.files import File

from common.llm.registry import LLMProviderRegistry
from common.services import BaseEmailService

from .agents import LogAnalysisAgent
from .contracts import LogReportResult
from .log_sources import LOG_SOURCES, REQUIRED_LOG_SOURCE
from .models import LogAnalysis

logger = logging.getLogger(__name__)
LogPathMap = dict[str, Optional[str]]


class DockerLogCollector:
    """Reads pre-collected logs from a volume-mounted directory.

    Logs are collected daily by `infra/scripts/monitoring/collect-logs.sh` (host cron job)
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
    def collect_logs(cls) -> LogPathMap:
        """Return paths to pre-collected log files from the mounted volume."""
        logs_dir: str = settings.DOCKER_LOGS_DIR

        cls._check_staleness(logs_dir)
        collected_paths: LogPathMap = {}
        size_by_key: dict[str, int] = {}

        for source in LOG_SOURCES:
            log_path = os.path.join(logs_dir, source.filename)
            if not os.path.exists(log_path):
                if source.required:
                    raise FileNotFoundError(
                        f"Log file not found: {log_path}. "
                        "Ensure the collect-logs.sh cron job has run successfully."
                    )
                logger.warning(
                    "%s not found in %s — %s logs will be skipped.",
                    source.filename,
                    logs_dir,
                    source.key,
                )
                collected_paths[source.key] = None
                size_by_key[source.key] = 0
                continue

            log_size = os.path.getsize(log_path)
            size_by_key[source.key] = log_size
            if log_size > 0 or source.required:
                collected_paths[source.key] = log_path
            else:
                collected_paths[source.key] = None
                logger.info(
                    "%s is empty in %s — %s logs will be skipped.",
                    source.filename,
                    logs_dir,
                    source.key,
                )

        size_report = ", ".join(
            f"{source.key}={size_by_key[source.key]} bytes" for source in LOG_SOURCES
        )
        logger.info("Read logs: %s", size_report)

        return collected_paths


class LogAnalyzer:
    """Analyzes logs using LLM agent."""

    def __init__(self, agent: LogAnalysisAgent):
        self.agent = agent

    def analyze_logs_from_files(
        self,
        log_paths: Mapping[str, Optional[str]],
        collected_at: str = "",
        historical_context: str = "",
    ) -> dict:
        """
        Analyze logs using LLM.

        Args:
            log_paths: Mapping of log source keys to file paths
            collected_at: ISO timestamp string from collected_at.txt
            historical_context: Pre-formatted string from HistoricalContextBuilder

        Returns:
            Analysis result dict with keys: summary, severity, key_findings,
            recommendations, trend_summary, gpt_tokens_used

        Raises:
            ValueError: If analysis returns empty result
        """
        result = self.agent.analyze_logs_from_files(
            log_paths,
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


class LogReportPreparationService:
    """Build a typed log report result from the existing analyzer output."""

    def __init__(self, analyzer: LogAnalyzer):
        self.analyzer = analyzer

    def prepare_report_from_files(
        self,
        log_paths: Mapping[str, Optional[str]],
        collected_at: str = "",
        historical_context: str = "",
    ) -> LogReportResult:
        raw_result: dict = self.analyzer.analyze_logs_from_files(
            log_paths,
            collected_at,
            historical_context=historical_context,
        )
        findings: object = raw_result.get("key_findings", [])
        normalized_findings: list[str]
        if isinstance(findings, list):
            normalized_findings = [str(item) for item in findings]
        elif isinstance(findings, str):
            normalized_findings = [findings]
        else:
            normalized_findings = []

        return LogReportResult(
            summary=str(raw_result.get("summary", "No summary provided")),
            severity=str(raw_result.get("severity", "INFO")),
            key_findings=normalized_findings,
            recommendations=str(raw_result.get("recommendations", "")),
            trend_summary=str(raw_result.get("trend_summary", "")),
            gpt_tokens_used=int(raw_result.get("gpt_tokens_used", 0)),
            gpt_cost_usd=float(raw_result.get("gpt_cost_usd", 0.0)),
        )


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
        analysis_date: date,
        log_paths: Mapping[str, Optional[str]],
    ) -> None:
        """
        Attach log files to the analysis record.

        Args:
            log_analysis: LogAnalysis instance to attach files to
            analysis_date: Date for filename generation
        """
        for source in LOG_SOURCES:
            log_path = log_paths.get(source.key)
            if not log_path or not os.path.exists(log_path):
                continue
            with open(log_path, "rb") as f:
                field_file = getattr(log_analysis, source.model_field)
                field_file.save(f"{source.key}_{analysis_date}.log", File(f))


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
        self.report_preparer = LogReportPreparationService(analyzer)
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
        log_paths: LogPathMap = {}

        try:
            log_paths, log_size = self._collect_logs()
            historical_context = self._build_historical_context(analysis_date)
            analysis_result = self._run_analysis(log_paths, historical_context)
            log_analysis = self._store_results(
                analysis_date,
                log_size,
                analysis_result,
                start_time,
                log_paths,
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
                log_paths,
            )
            raise

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _collect_logs(self) -> tuple[LogPathMap, int]:
        """Collect log files and return paths plus total byte size."""
        raw_log_paths = self.collector.collect_logs()
        log_paths = self._normalize_collected_logs(raw_log_paths)
        log_size = sum(os.path.getsize(path) for path in log_paths.values() if path)
        if log_size == 0:
            logger.warning("No logs collected from Docker containers")
        return log_paths, log_size

    def _normalize_collected_logs(self, raw_log_paths: object) -> LogPathMap:
        """Accept both registry-based mappings and legacy tuple collector output."""
        if isinstance(raw_log_paths, Mapping):
            return dict(raw_log_paths)

        if isinstance(raw_log_paths, tuple):
            normalized: LogPathMap = {}
            for source, path_value in zip(LOG_SOURCES, raw_log_paths):
                normalized[source.key] = path_value if isinstance(path_value, str) else None
            for source in LOG_SOURCES:
                normalized.setdefault(source.key, None)
            return normalized

        raise TypeError(
            "DockerLogCollector.collect_logs() must return a mapping of log keys to paths "
            f"or a legacy tuple, got {type(raw_log_paths).__name__}"
        )

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
        log_paths: Mapping[str, Optional[str]],
        historical_context: str,
    ) -> LogReportResult:
        """Run LLM analysis and return the typed log report result."""
        collected_at = self.collector.get_collected_at()
        return self.report_preparer.prepare_report_from_files(
            log_paths,
            collected_at,
            historical_context=historical_context,
        )

    def _store_results(
        self,
        analysis_date: date,
        log_size: int,
        analysis_result: LogReportResult,
        start_time: float,
        log_paths: Mapping[str, Optional[str]],
    ) -> LogAnalysis:
        """Persist analysis results and attach log files."""
        log_analysis = self.storage.create_or_replace_analysis(
            analysis_date=analysis_date,
            log_size_bytes=log_size,
            summary=analysis_result.summary,
            severity=analysis_result.severity,
            key_findings=analysis_result.key_findings,
            recommendations=analysis_result.recommendations,
            trend_summary=analysis_result.trend_summary,
            execution_time_seconds=time.time() - start_time,
            gpt_tokens_used=analysis_result.gpt_tokens_used,
            gpt_cost_usd=analysis_result.gpt_cost_usd,
        )
        self.storage.attach_log_files(log_analysis, analysis_date, log_paths)
        return log_analysis

    def _store_error(
        self,
        analysis_date: date,
        error: Exception,
        start_time: float,
        log_paths: Mapping[str, Optional[str]] | None = None,
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
        if log_paths and log_paths.get(REQUIRED_LOG_SOURCE.key):
            self.storage.attach_log_files(log_analysis, analysis_date, log_paths)

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
