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
from .log_sources import LOG_SOURCES, REQUIRED_LOG_SOURCE
from .models import LogAnalysis
from .monitoring_agent_runner import MonitoringToolLoopRunner
from .types import (
    JSONValue,
    LogAnalysisPayload,
    LogReportResult,
    MonitoringFindingsValue,
    MonitoringJobName,
    RawCollectedLogPaths,
)

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
        collected_at_path: str = os.path.join(logs_dir, "collected_at.txt")
        if not os.path.exists(collected_at_path):
            logger.warning(
                "collected_at.txt not found in %s — cron job may not have run yet",
                logs_dir,
            )
            return
        with open(collected_at_path) as f:
            collected_at_raw: str = f.read().strip()
        collected_at: datetime = datetime.fromisoformat(collected_at_raw).replace(
            tzinfo=timezone.utc
        )
        age_hours: float = (datetime.now(timezone.utc) - collected_at).total_seconds() / 3600
        if age_hours > cls.MAX_STALENESS_HOURS:
            logger.warning(
                "Docker logs are %.1f hours old (expected <%d h) — cron job may have missed a run",
                age_hours,
                cls.MAX_STALENESS_HOURS,
            )

    @classmethod
    def get_collected_at(cls) -> str:
        """Return the raw ISO timestamp from collected_at.txt, or empty string if missing."""
        path: str = os.path.join(settings.DOCKER_LOGS_DIR, "collected_at.txt")
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
            log_path: str = os.path.join(logs_dir, source.filename)
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

            log_size: int = os.path.getsize(log_path)
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

        size_report: str = ", ".join(
            f"{source.key}={size_by_key[source.key]} bytes" for source in LOG_SOURCES
        )
        logger.info("Read logs: %s", size_report)

        return collected_paths


class LogAnalyzer:
    """Analyzes logs using LLM agent."""

    def __init__(self, agent: LogAnalysisAgent):
        self.agent: LogAnalysisAgent = agent

    def analyze_logs_from_files(
        self,
        log_paths: Mapping[str, Optional[str]],
        collected_at: str = "",
        historical_context: str = "",
    ) -> LogAnalysisPayload:
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
        raw_result: dict[str, JSONValue] | None = self.agent.analyze_logs_from_files(
            log_paths,
            collected_at,
            historical_context=historical_context,
        )
        if not raw_result:
            raise ValueError("LLM analysis returned empty result")

        tokens_raw: JSONValue = raw_result.get("gpt_tokens_used", 0)
        cost_raw: JSONValue = raw_result.get("gpt_cost_usd", 0.0)
        normalized_tokens: int = int(tokens_raw) if isinstance(tokens_raw, (int, float, str)) else 0
        normalized_cost: float = float(cost_raw) if isinstance(cost_raw, (int, float, str)) else 0.0
        normalized_result: LogAnalysisPayload = {
            "summary": str(raw_result.get("summary", "")),
            "severity": str(raw_result.get("severity", "")),
            "recommendations": str(raw_result.get("recommendations", "")),
            "trend_summary": str(raw_result.get("trend_summary", "")),
            "gpt_tokens_used": normalized_tokens,
            "gpt_cost_usd": normalized_cost,
        }
        findings: JSONValue = raw_result.get("key_findings", [])
        if isinstance(findings, list):
            normalized_result["key_findings"] = [str(item) for item in findings]
        elif isinstance(findings, str):
            normalized_result["key_findings"] = findings
        return normalized_result


class LogReportPreparationService:
    """Build a typed log report result from the existing analyzer output."""

    def __init__(self, analyzer: LogAnalyzer):
        self.analyzer: LogAnalyzer = analyzer

    def prepare_report_from_files(
        self,
        log_paths: Mapping[str, Optional[str]],
        collected_at: str = "",
        historical_context: str = "",
    ) -> LogReportResult:
        raw_result: LogAnalysisPayload = self.analyzer.analyze_logs_from_files(
            log_paths,
            collected_at,
            historical_context=historical_context,
        )
        findings: MonitoringFindingsValue | JSONValue = raw_result.get("key_findings", [])
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
        existing_count: int = LogAnalysis.objects.for_date(analysis_date).count()
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
            log_path: str | None = log_paths.get(source.key)
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
        deleted_count: int
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
        lines: list[str] = []
        for record in records:
            lines.append(
                f"## {record.analysis_date} \u2014 Severity: {record.severity}\n"
                f"Summary: {record.summary}\n"
                f"Key findings: {record.key_findings}\n"
                f"Recommendations: {record.recommendations}"
            )
        return "\n\n".join(lines)


class LogAnalysisOrchestrator:
    """Legacy log-analysis orchestrator kept as the compatibility boundary.

    This class represents the original direct LLM log-analysis path. It stays
    in place while the bounded monitoring-agent runtime is validated end to
    end. Once the agent-driven path fully replaces it, this orchestrator is
    expected to be removed.
    """

    def __init__(
        self,
        collector: DockerLogCollector,
        analyzer: LogAnalyzer,
        storage: LogStorageService,
    ):
        self.collector: DockerLogCollector = collector
        self.analyzer: LogAnalyzer = analyzer
        self.report_preparer: LogReportPreparationService = LogReportPreparationService(analyzer)
        self.storage: LogStorageService = storage

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

        start_time: float = time.time()
        log_paths: LogPathMap = {}

        try:
            log_paths, log_size = self._collect_logs()
            historical_context: str = self._build_historical_context(analysis_date)
            analysis_result: LogReportResult = self._run_analysis(log_paths, historical_context)
            log_analysis: LogAnalysis = self._store_results(
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
        raw_log_paths: RawCollectedLogPaths = self.collector.collect_logs()
        log_paths: LogPathMap = self._normalize_collected_logs(raw_log_paths)
        log_size: int = sum(os.path.getsize(path) for path in log_paths.values() if path)
        if log_size == 0:
            logger.warning("No logs collected from Docker containers")
        return log_paths, log_size

    def _normalize_collected_logs(self, raw_log_paths: RawCollectedLogPaths) -> LogPathMap:
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
        historical_context: str = HistoricalContextBuilder.build(exclude_date=analysis_date)
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
        collected_at: str = self.collector.get_collected_at()
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
        execution_time_seconds: float = time.time() - start_time
        log_analysis: LogAnalysis = self.storage.create_or_replace_analysis(
            analysis_date=analysis_date,
            log_size_bytes=log_size,
            summary=analysis_result.summary,
            severity=analysis_result.severity,
            key_findings=analysis_result.key_findings,
            recommendations=analysis_result.recommendations,
            trend_summary=analysis_result.trend_summary,
            execution_time_seconds=execution_time_seconds,
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
        execution_time_seconds: float = time.time() - start_time
        log_analysis: LogAnalysis = self.storage.create_or_replace_analysis(
            analysis_date=analysis_date,
            backend_logs=None,
            frontend_logs=None,
            error_message=str(error),
            execution_time_seconds=execution_time_seconds,
            severity=LogAnalysis.Severity.CRITICAL,
            summary=f"Analysis Failed: {str(error)}",
        )
        if log_paths and log_paths.get(REQUIRED_LOG_SOURCE.key):
            self.storage.attach_log_files(log_analysis, analysis_date, log_paths)

    @classmethod
    def create_default(cls) -> "LogAnalysisOrchestrator":
        """Factory method to create orchestrator with default dependencies."""

        # Fail-fast: No defaults, settings must be explicit
        provider_name: str = settings.MONITORING_LLM_PROVIDER
        provider = LLMProviderRegistry.get(provider_name)
        agent: LogAnalysisAgent = LogAnalysisAgent(provider)

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
        self.log_analysis: LogAnalysis = log_analysis

    def get_subject(self) -> str:
        """Generate email subject line."""
        return self.log_analysis.get_email_subject()

    def get_context(self) -> dict:
        """Generate template context dictionary."""
        return self.log_analysis.get_email_context()

    def get_template_name(self) -> str:
        """Return path to email template."""
        return "monitoring/email/log_analysis.html"


class MonitoringAgentLogOrchestrator:
    """Run the bounded monitoring-agent flow for daily log analysis.

    This orchestrator preserves the current compatibility boundary:
    - deterministic log collection still happens first
    - the existing typed log report is still prepared first
    - the bounded monitoring agent runs on top of that prepared report
    - persistence and email rendering still reuse the existing LogAnalysis path
    """

    def __init__(
        self,
        collector: DockerLogCollector,
        analyzer: LogAnalyzer,
        storage: LogStorageService,
        agent_runner: MonitoringToolLoopRunner,
    ) -> None:
        self.collector: DockerLogCollector = collector
        self.analyzer: LogAnalyzer = analyzer
        self.report_preparer: LogReportPreparationService = LogReportPreparationService(analyzer)
        self.storage: LogStorageService = storage
        self.agent_runner: MonitoringToolLoopRunner = agent_runner

    def analyze_and_store(self, analysis_date: Optional[date] = None) -> LogAnalysis:
        """Collect logs, run the bounded monitoring agent, and persist results."""
        if analysis_date is None:
            analysis_date = date.today()

        start_time: float = time.time()
        log_paths: LogPathMap = {}

        try:
            log_paths, log_size = self._collect_logs()
            historical_context: str = self._build_historical_context(analysis_date)
            deterministic_report: LogReportResult = self._prepare_report(
                log_paths,
                historical_context,
            )
            final_report: LogReportResult = self._run_monitoring_agent(deterministic_report)
            log_analysis: LogAnalysis = self._store_results(
                analysis_date,
                log_size,
                final_report,
                start_time,
                log_paths,
            )
            logger.info(
                "Monitoring agent log analysis complete for %s: record_id=%s, severity=%s",
                analysis_date,
                log_analysis.id,
                log_analysis.severity,
            )
            return log_analysis

        except Exception as error:
            logger.exception("Monitoring agent log analysis failed for date %s", analysis_date)
            self._store_error(
                analysis_date,
                error,
                start_time,
                log_paths,
            )
            raise

    def _collect_logs(self) -> tuple[LogPathMap, int]:
        """Collect log files and return paths plus total byte size."""
        raw_log_paths: RawCollectedLogPaths = self.collector.collect_logs()
        log_paths: LogPathMap = self._normalize_collected_logs(raw_log_paths)
        log_size: int = sum(os.path.getsize(path) for path in log_paths.values() if path)
        if log_size == 0:
            logger.warning("No logs collected from Docker containers")
        return log_paths, log_size

    def _build_historical_context(self, analysis_date: date) -> str:
        """Build the last-5-days monitoring context used by the current log flow."""
        historical_context: str = HistoricalContextBuilder.build(exclude_date=analysis_date)
        if historical_context:
            logger.info(
                "Historical context loaded for monitoring agent (%d chars)", len(historical_context)
            )
        else:
            logger.info("No historical context available for monitoring agent")
        return historical_context

    def _prepare_report(
        self,
        log_paths: Mapping[str, Optional[str]],
        historical_context: str,
    ) -> LogReportResult:
        """Prepare the deterministic log report that seeds the agent runtime."""
        collected_at: str = self.collector.get_collected_at()
        return self.report_preparer.prepare_report_from_files(
            log_paths,
            collected_at,
            historical_context=historical_context,
        )

    def _run_monitoring_agent(self, deterministic_report: LogReportResult) -> LogReportResult:
        """Run the bounded monitoring agent and normalize its final structured output."""
        loop_result = self.agent_runner.run(
            job_name=self._get_job_name(),
            job_context={
                "log_report": deterministic_report.to_payload(),
            },
        )
        final_payload = loop_result.final_payload

        findings_default: JSONValue = [finding for finding in loop_result.findings]
        findings_raw: JSONValue = final_payload.get(
            "key_findings",
            findings_default,
        )
        key_findings: list[str]
        if isinstance(findings_raw, list):
            key_findings = [str(item) for item in findings_raw]
        elif isinstance(findings_raw, str):
            key_findings = [findings_raw]
        else:
            key_findings = deterministic_report.key_findings

        return LogReportResult(
            summary=str(
                final_payload.get("summary", loop_result.summary or deterministic_report.summary)
            ),
            severity=str(final_payload.get("severity", deterministic_report.severity)),
            key_findings=key_findings or deterministic_report.key_findings,
            recommendations=str(
                final_payload.get("recommendations", deterministic_report.recommendations)
            ),
            trend_summary=str(
                final_payload.get("trend_summary", deterministic_report.trend_summary)
            ),
            gpt_tokens_used=deterministic_report.gpt_tokens_used,
            gpt_cost_usd=deterministic_report.gpt_cost_usd,
        )

    def _store_results(
        self,
        analysis_date: date,
        log_size: int,
        analysis_result: LogReportResult,
        start_time: float,
        log_paths: Mapping[str, Optional[str]],
    ) -> LogAnalysis:
        """Persist the final monitoring-agent report through the existing model path."""
        execution_time_seconds: float = time.time() - start_time
        log_analysis: LogAnalysis = self.storage.create_or_replace_analysis(
            analysis_date=analysis_date,
            log_size_bytes=log_size,
            summary=analysis_result.summary,
            severity=analysis_result.severity,
            key_findings=analysis_result.key_findings,
            recommendations=analysis_result.recommendations,
            trend_summary=analysis_result.trend_summary,
            execution_time_seconds=execution_time_seconds,
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
        """Persist a CRITICAL record when the agent-driven flow fails."""
        execution_time_seconds: float = time.time() - start_time
        log_analysis: LogAnalysis = self.storage.create_or_replace_analysis(
            analysis_date=analysis_date,
            backend_logs=None,
            frontend_logs=None,
            error_message=str(error),
            execution_time_seconds=execution_time_seconds,
            severity=LogAnalysis.Severity.CRITICAL,
            summary=f"Analysis Failed: {str(error)}",
        )
        if log_paths and log_paths.get(REQUIRED_LOG_SOURCE.key):
            self.storage.attach_log_files(log_analysis, analysis_date, log_paths)

    @staticmethod
    def _normalize_collected_logs(raw_log_paths: RawCollectedLogPaths) -> LogPathMap:
        """Accept both registry-based mappings and the legacy tuple collector output."""
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

    @staticmethod
    def _get_job_name() -> MonitoringJobName:
        """Return the monitoring job name used by the bounded agent runner."""
        return MonitoringJobName.LOG_REPORT

    @classmethod
    def create_default(cls) -> "MonitoringAgentLogOrchestrator":
        """Create the default monitoring-agent log orchestrator with real provider wiring."""
        provider_name: str = settings.MONITORING_LLM_PROVIDER
        provider = LLMProviderRegistry.get(provider_name)
        agent: LogAnalysisAgent = LogAnalysisAgent(provider)
        agent_runner: MonitoringToolLoopRunner = MonitoringToolLoopRunner(provider=provider)
        return cls(
            collector=DockerLogCollector(),
            analyzer=LogAnalyzer(agent),
            storage=LogStorageService(),
            agent_runner=agent_runner,
        )
