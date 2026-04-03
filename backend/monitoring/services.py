import json
import logging
import os
import re
import time
from collections.abc import Mapping
from datetime import UTC, date, datetime

from django.conf import settings
from django.core.files import File

from common.llm.protocols import LLMProvider
from common.llm.registry import LLMProviderRegistry
from common.services import BaseEmailService

from .agents import LogAnalysisAgent
from .log_sources import LOG_SOURCES, REQUIRED_LOG_SOURCE
from .models import LogAnalysis, SitemapAnalysis
from .monitoring_agent_runner import MonitoringToolLoopRunner
from .prompt_assets import PromptAssetLoader
from .sitemap_services import SitemapAuditService, SitemapHTTPClient
from .types import (
    JSONObject,
    JSONValue,
    LogAnalysisPayload,
    LogReportResult,
    MonitoringFindingsValue,
    MonitoringJobName,
    RawCollectedLogPaths,
    SitemapIssue,
    SitemapReportResult,
    SitemapSummaryResult,
)

logger = logging.getLogger(__name__)
LogPathMap = dict[str, str | None]


def normalize_text_value(value: JSONValue, default: str = "") -> str:
    """Normalize LLM payload text fields into readable plain text."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        text_items: list[str] = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(text_items)
    if value is None:
        return default
    return str(value)


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
        with open(collected_at_path, encoding="utf-8") as f:
            collected_at_raw: str = f.read().strip()
        collected_at: datetime = datetime.fromisoformat(collected_at_raw).replace(tzinfo=UTC)
        age_hours: float = (datetime.now(UTC) - collected_at).total_seconds() / 3600
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
            with open(path, encoding="utf-8") as f:
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
        log_paths: Mapping[str, str | None],
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
            "recommendations": normalize_text_value(raw_result.get("recommendations", "")),
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
        log_paths: Mapping[str, str | None],
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
            recommendations=normalize_text_value(raw_result.get("recommendations", "")),
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
        execution_time_raw: object | None = kwargs.get("execution_time_seconds")
        if isinstance(execution_time_raw, (int, float)):
            kwargs["execution_time_seconds"] = round(float(execution_time_raw), 2)
        return LogAnalysis.objects.create(analysis_date=analysis_date, **kwargs)

    @classmethod
    def attach_log_files(
        cls,
        log_analysis: LogAnalysis,
        analysis_date: date,
        log_paths: Mapping[str, str | None],
    ) -> None:
        """
        Attach log files to the analysis record.

        Args:
            log_analysis: LogAnalysis instance to attach files to
            analysis_date: Date for filename generation
            log_paths: Mapping of log source keys to filesystem paths for collected logs
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

    def analyze_and_store(self, analysis_date: date | None = None) -> LogAnalysis:
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
            for source, path_value in zip(LOG_SOURCES, raw_log_paths, strict=False):
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
        log_paths: Mapping[str, str | None],
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
        log_paths: Mapping[str, str | None],
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
        log_paths: Mapping[str, str | None] | None = None,
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


class SitemapSummaryService:
    """Summarize deterministic sitemap findings with the configured LLM provider."""

    def __init__(
        self,
        provider: LLMProvider,
        asset_loader: PromptAssetLoader | None = None,
    ) -> None:
        self.provider: LLMProvider = provider
        self.asset_loader: PromptAssetLoader = asset_loader or PromptAssetLoader()

    def summarize(self, report: SitemapReportResult) -> SitemapSummaryResult:
        if not report.issues:
            logger.info("Skipping sitemap LLM summary because deterministic audit is clean")
            return self._build_fallback_summary(report)

        system_prompt: str = self._build_system_prompt()
        user_message: str = self._build_user_message(report)
        response_text, usage = self.provider.ask_question_with_usage(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.0,
        )

        if not response_text:
            return self._build_fallback_summary(report)

        try:
            payload: JSONObject = self._parse_response(response_text)
        except Exception:
            logger.exception("Failed to parse sitemap LLM summary, using deterministic fallback")
            return self._build_fallback_summary(report)

        findings_raw: JSONValue = payload.get("key_findings", [])
        key_findings: list[str]
        if isinstance(findings_raw, list):
            key_findings = [str(item) for item in findings_raw]
        elif isinstance(findings_raw, str):
            key_findings = [findings_raw]
        else:
            key_findings = []

        return SitemapSummaryResult(
            summary=str(payload.get("summary", self._build_fallback_summary(report).summary)),
            severity=str(payload.get("severity", self._build_default_severity(report))),
            key_findings=key_findings,
            recommendations=normalize_text_value(payload.get("recommendations", "")),
            trend_summary=str(payload.get("trend_summary", "")),
            gpt_tokens_used=int(usage.get("total_tokens", 0)),
            gpt_cost_usd=float(usage.get("cost_usd", 0.0)),
        )

    def _build_system_prompt(self) -> str:
        summary_prompt: str = self.asset_loader.load_text("prompts/monitoring_sitemap_summary.md")
        return "\n\n".join(
            [
                summary_prompt.strip(),
                (
                    "Return a single JSON object with keys: "
                    "summary, severity, key_findings, recommendations, trend_summary."
                ),
                "Severity must be one of INFO, WARNING, CRITICAL.",
                "Do not wrap the JSON in markdown fences.",
            ]
        )

    def _build_user_message(self, report: SitemapReportResult) -> str:
        payload: JSONObject = {
            "root_sitemap_url": report.root_sitemap_url,
            "total_sitemaps": report.total_sitemaps,
            "total_urls": report.total_urls,
            "issue_summary": self._summarize_issues(report.issues),
            "issues": [self._serialize_issue(issue) for issue in report.issues],
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    def _summarize_issues(self, issues: list[SitemapIssue]) -> JSONObject:
        counts: JSONObject = {}
        for issue in issues:
            current_count_raw: JSONValue = counts.get(issue.category.value, 0)
            current_count: int = (
                int(current_count_raw) if isinstance(current_count_raw, (int, float, str)) else 0
            )
            counts[issue.category.value] = current_count + 1
        return counts

    def _serialize_issue(self, issue: SitemapIssue) -> JSONObject:
        payload: JSONObject = {
            "url": issue.url,
            "category": issue.category.value,
            "message": issue.message,
        }
        if issue.status_code is not None:
            payload["status_code"] = issue.status_code
        if issue.final_url is not None:
            payload["final_url"] = issue.final_url
        return payload

    def _build_default_severity(self, report: SitemapReportResult) -> str:
        if not report.issues:
            return SitemapAnalysis.Severity.INFO
        if any(issue.category.value in {"broken_url", "fetch_error"} for issue in report.issues):
            return SitemapAnalysis.Severity.CRITICAL
        return SitemapAnalysis.Severity.WARNING

    def _build_fallback_summary(self, report: SitemapReportResult) -> SitemapSummaryResult:
        issue_summary: dict[str, int] = {
            key: value
            for key, value in self._summarize_issues(report.issues).items()
            if isinstance(value, int)
        }
        if not report.issues:
            return SitemapSummaryResult(
                summary="Sitemap audit completed with no issues detected.",
                severity=SitemapAnalysis.Severity.INFO,
                key_findings=["All sitemap URLs resolved without deterministic issues."],
                recommendations="No action needed.",
                trend_summary="No sitemap issues were detected in this run.",
            )

        key_findings: list[str] = [
            f"{category.replace('_', ' ')}: {count}"
            for category, count in sorted(issue_summary.items())
        ]
        return SitemapSummaryResult(
            summary=(
                f"Sitemap audit completed with {len(report.issues)} issue(s) "
                f"across {report.total_urls} URL(s)."
            ),
            severity=self._build_default_severity(report),
            key_findings=key_findings,
            recommendations="Review the deterministic sitemap issues and fix the affected URLs.",
            trend_summary="Trend summary unavailable because the sitemap LLM summary was skipped.",
        )

    @staticmethod
    def _load_json_object(raw_text: str, error_message: str) -> JSONObject:
        try:
            payload: JSONValue = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(error_message) from exc

        if not isinstance(payload, dict):
            raise ValueError(error_message)
        return payload

    def _parse_response(self, response_text: str) -> JSONObject:
        error_message = "Sitemap summary response must be a JSON object"
        try:
            return self._load_json_object(response_text, error_message)
        except json.JSONDecodeError as exc:
            match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if match:
                return self._load_json_object(match.group(1), error_message)
            start_index: int = response_text.find("{")
            end_index: int = response_text.rfind("}")
            if start_index != -1 and end_index != -1:
                return self._load_json_object(
                    response_text[start_index : end_index + 1],
                    error_message,
                )
            raise ValueError(error_message) from exc


class SitemapAnalysisStorageService:
    """Store sitemap analysis results independently from daily log analyses."""

    @classmethod
    def create_or_replace_analysis(
        cls,
        analysis_date: date,
        report: SitemapReportResult,
        summary: SitemapSummaryResult,
        execution_time_seconds: float,
    ) -> SitemapAnalysis:
        rounded_execution_time_seconds: float = round(execution_time_seconds, 2)
        existing_count: int = SitemapAnalysis.objects.filter(analysis_date=analysis_date).count()
        if existing_count > 0:
            logger.info(
                "Replacing %d existing sitemap analysis record(s) for %s",
                existing_count,
                analysis_date,
            )
            SitemapAnalysis.objects.filter(analysis_date=analysis_date).delete()
        issue_summary: dict[str, int] = {}
        serialized_issues: list[dict[str, JSONValue]] = []
        for issue in report.issues:
            issue_summary[issue.category.value] = issue_summary.get(issue.category.value, 0) + 1
            serialized_issues.append(
                {
                    "url": issue.url,
                    "category": issue.category.value,
                    "message": issue.message,
                    "status_code": issue.status_code,
                    "final_url": issue.final_url,
                }
            )

        analysis = SitemapAnalysis.objects.create(
            analysis_date=analysis_date,
            root_sitemap_url=report.root_sitemap_url,
            total_sitemaps=report.total_sitemaps,
            total_urls=report.total_urls,
            issue_summary=issue_summary,
            issues=serialized_issues,
            summary=summary.summary,
            severity=summary.severity,
            key_findings=summary.key_findings,
            recommendations=summary.recommendations,
            trend_summary=summary.trend_summary,
            execution_time_seconds=rounded_execution_time_seconds,
            gpt_tokens_used=summary.gpt_tokens_used,
            gpt_cost_usd=summary.gpt_cost_usd,
            email_sent=False,
            error_message="",
        )
        return analysis


class SitemapAnalysisEmailService(BaseEmailService):
    """Generate and send the sitemap analysis email."""

    def __init__(self, sitemap_analysis: SitemapAnalysis) -> None:
        self.sitemap_analysis: SitemapAnalysis = sitemap_analysis

    def get_subject(self) -> str:
        return self.sitemap_analysis.get_email_subject()

    def get_context(self) -> dict:
        return self.sitemap_analysis.get_email_context()

    def get_template_name(self) -> str:
        return "monitoring/email/sitemap_analysis.html"


class SitemapAnalysisOrchestrator:
    """Run deterministic sitemap auditing and summarize it with the configured LLM."""

    def __init__(
        self,
        audit_service: SitemapAuditService,
        summary_service: SitemapSummaryService,
        storage: SitemapAnalysisStorageService,
    ) -> None:
        self.audit_service: SitemapAuditService = audit_service
        self.summary_service: SitemapSummaryService = summary_service
        self.storage: SitemapAnalysisStorageService = storage

    def analyze_and_store(self, analysis_date: date | None = None) -> SitemapAnalysis:
        if analysis_date is None:
            analysis_date = date.today()

        start_time: float = time.time()
        try:
            sitemap_report: SitemapReportResult = self.audit_service.audit()
            summary: SitemapSummaryResult = self.summary_service.summarize(sitemap_report)
            execution_time_seconds: float = time.time() - start_time
            sitemap_analysis: SitemapAnalysis = self.storage.create_or_replace_analysis(
                analysis_date=analysis_date,
                report=sitemap_report,
                summary=summary,
                execution_time_seconds=execution_time_seconds,
            )
            logger.info(
                "Sitemap analysis complete for %s: record_id=%s severity=%s",
                analysis_date,
                sitemap_analysis.id,
                sitemap_analysis.severity,
            )
            return sitemap_analysis
        except Exception as error:
            logger.exception("Sitemap analysis failed for date %s", analysis_date)
            existing_count: int = SitemapAnalysis.objects.filter(
                analysis_date=analysis_date
            ).count()
            if existing_count > 0:
                SitemapAnalysis.objects.filter(analysis_date=analysis_date).delete()
            rounded_execution_time_seconds: float = round(time.time() - start_time, 2)
            return SitemapAnalysis.objects.create(
                analysis_date=analysis_date,
                root_sitemap_url=self.audit_service.get_default_sitemap_url(),
                summary=f"Analysis Failed: {error}",
                severity=SitemapAnalysis.Severity.CRITICAL,
                error_message=str(error),
                execution_time_seconds=rounded_execution_time_seconds,
            )

    @classmethod
    def create_default(cls) -> "SitemapAnalysisOrchestrator":
        provider_name: str = settings.MONITORING_LLM_PROVIDER
        provider = LLMProviderRegistry.get(provider_name)
        production_domain: str = settings.SITE_DOMAIN
        http_client = SitemapHTTPClient(
            verify_ssl=not settings.DEBUG,
            internal_base_url="http://nginx" if settings.DEBUG else None,
            public_host=production_domain,
        )
        audit_service = SitemapAuditService(
            client=http_client,
            production_domain=production_domain,
        )
        summary_service = SitemapSummaryService(provider=provider)
        return cls(
            audit_service=audit_service,
            summary_service=summary_service,
            storage=SitemapAnalysisStorageService(),
        )


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

    def analyze_and_store(self, analysis_date: date | None = None) -> LogAnalysis:
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
        log_paths: Mapping[str, str | None],
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
            recommendations=normalize_text_value(
                final_payload.get("recommendations", deterministic_report.recommendations),
                deterministic_report.recommendations,
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
        log_paths: Mapping[str, str | None],
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
        log_paths: Mapping[str, str | None] | None = None,
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
            for source, path_value in zip(LOG_SOURCES, raw_log_paths, strict=False):
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
