# backend/monitoring/services.py
import logging
import os
import shutil
import subprocess
import time
from datetime import date
from typing import Optional

from django.conf import settings
from django.core.files import File

from common.llm.registry import LLMProviderRegistry
from common.services import BaseEmailService

from .agents import LogAnalysisAgent
from .models import LogAnalysis

logger = logging.getLogger(__name__)


class DockerLogCollector:
    """Collects logs from Docker containers."""

    _docker_path: Optional[str] = None  # Cache docker executable path

    @classmethod
    def _get_docker_path(cls) -> str:
        """
        Find docker executable path with caching.

        Returns:
            str: Absolute path to docker executable

        Raises:
            FileNotFoundError: If docker is not found
        """
        if cls._docker_path:
            return cls._docker_path

        docker_path = shutil.which("docker")

        if not docker_path:
            # Fallback to common locations
            for candidate in ["/usr/local/bin/docker", "/usr/bin/docker"]:
                if os.path.exists(candidate):
                    docker_path = candidate
                    break
            else:
                raise FileNotFoundError(
                    "Could not find 'docker' executable. "
                    "Please ensure Docker is installed and in PATH."
                )

        cls._docker_path = docker_path
        logger.info("Docker executable found at: %s", docker_path)
        return docker_path

    @classmethod
    def collect_logs(cls) -> tuple[str, str]:
        """
        Collect logs from Docker containers and write to temp files.

        Returns:
            Tuple of (backend_log_path, frontend_log_path)

        Raises:
            FileNotFoundError: If docker executable not found
            subprocess.TimeoutExpired: If collection times out
            subprocess.CalledProcessError: If docker command fails
        """
        logger.info("Collecting Docker logs to temporary files")

        try:
            # Get project directory from settings
            project_dir = settings.PROJECT_ROOT

            # Find docker executable
            docker_path = cls._get_docker_path()

            timestamp = int(time.time())
            backend_log_path = f"/tmp/backend_{timestamp}.log"
            frontend_log_path = f"/tmp/frontend_{timestamp}.log"

            # Backend logs - stream to file
            with open(backend_log_path, "w") as f:
                subprocess.run(
                    [docker_path, "compose", "logs", "--tail=2000", "portfolio-be"],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=45,
                    check=True,
                    cwd=project_dir,
                    env={
                        **os.environ,
                        "PATH": "/usr/local/bin:/usr/bin:/bin:" + os.environ.get("PATH", ""),
                    },
                )

            # Frontend logs - stream to file
            with open(frontend_log_path, "w") as f:
                subprocess.run(
                    [docker_path, "compose", "logs", "--tail=2000", "portfolio-fe"],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=45,
                    check=True,
                    cwd=project_dir,
                    env={
                        **os.environ,
                        "PATH": "/usr/local/bin:/usr/bin:/bin:" + os.environ.get("PATH", ""),
                    },
                )

            # Check file sizes
            be_size = os.path.getsize(backend_log_path)
            fe_size = os.path.getsize(frontend_log_path)

            logger.info("Collected logs: backend=%d bytes, frontend=%d bytes", be_size, fe_size)

            return backend_log_path, frontend_log_path

        except subprocess.TimeoutExpired:
            logger.error("Docker logs collection timed out")
            raise
        except subprocess.CalledProcessError as e:
            logger.error("Docker command failed: %s", e)
            raise


class LogAnalyzer:
    """Analyzes logs using LLM agent."""

    def __init__(self, agent: LogAnalysisAgent):
        self.agent = agent

    def analyze_logs_from_files(self, backend_log_path: str, frontend_log_path: str) -> dict:
        """
        Analyze logs using LLM.

        Args:
            backend_log_path: Path to backend log file
            frontend_log_path: Path to frontend log file

        Returns:
            Analysis result dict with keys: summary, severity, key_findings,
            recommendations, gpt_tokens_used

        Raises:
            ValueError: If analysis returns empty result
        """
        result = self.agent.analyze_logs_from_files(backend_log_path, frontend_log_path)

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
    ) -> None:
        """
        Attach log files to the analysis record.

        Args:
            log_analysis: LogAnalysis instance to attach files to
            backend_path: Path to backend log file
            frontend_path: Path to frontend log file
            analysis_date: Date for filename generation
        """
        with open(backend_path, "rb") as f:
            log_analysis.backend_logs.save(f"backend_{analysis_date}.log", File(f))

        with open(frontend_path, "rb") as f:
            log_analysis.frontend_logs.save(f"frontend_{analysis_date}.log", File(f))


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

        try:
            # 1. Collect logs
            backend_log_path, frontend_log_path = self.collector.collect_logs()
            log_size = os.path.getsize(backend_log_path) + os.path.getsize(frontend_log_path)

            if log_size == 0:
                logger.warning("No logs collected from Docker containers")

            # 2. Analyze with LLM
            analysis_result = self.analyzer.analyze_logs_from_files(
                backend_log_path, frontend_log_path
            )

            # 3. Store in database
            log_analysis = self.storage.create_or_replace_analysis(
                analysis_date=analysis_date,
                log_size_bytes=log_size,
                summary=analysis_result.get("summary", "No summary provided"),
                severity=analysis_result.get("severity", "INFO"),
                key_findings=analysis_result.get("key_findings", []),
                recommendations=analysis_result.get("recommendations", ""),
                execution_time_seconds=time.time() - start_time,
                gpt_tokens_used=analysis_result.get("gpt_tokens_used", 0),
            )

            # 4. Attach log files
            self.storage.attach_log_files(
                log_analysis, backend_log_path, frontend_log_path, analysis_date
            )

            logger.info(
                "Log analysis complete for %s: record_id=%s, severity=%s",
                analysis_date,
                log_analysis.id,
                log_analysis.severity,
            )
            return log_analysis

        except Exception as e:
            logger.exception("Log analysis failed for date %s", analysis_date)
            # Store error
            log_analysis = self.storage.create_or_replace_analysis(
                analysis_date=analysis_date,
                backend_logs=None,
                frontend_logs=None,
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
                severity=LogAnalysis.Severity.CRITICAL,
                summary=f"Analysis Failed: {str(e)}",
            )
            raise
        finally:
            # Cleanup temp files
            if backend_log_path and os.path.exists(backend_log_path):
                os.remove(backend_log_path)
            if frontend_log_path and os.path.exists(frontend_log_path):
                os.remove(frontend_log_path)

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
