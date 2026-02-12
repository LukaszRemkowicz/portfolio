import logging
import os
import shutil
import subprocess
import time
from datetime import date, timedelta
from typing import Optional

from django.conf import settings
from django.core.files import File
from django.template.loader import render_to_string

from common.llm.factory import get_llm_provider
from common.services import EmailService

from .agents import LogAnalysisAgent
from .models import LogAnalysis

logger = logging.getLogger(__name__)


class LogCollectionService:
    """Service for collecting and analyzing Docker logs."""

    agent: Optional[LogAnalysisAgent] = None
    _docker_path: Optional[str] = None  # Cache docker executable path

    @classmethod
    def _get_docker_path(cls) -> str:
        """
        Finds docker executable path with caching.

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
    def _get_agent(cls) -> LogAnalysisAgent:
        """Lazy-load log analysis agent with configured LLM provider."""
        if cls.agent is None:
            provider = get_llm_provider()
            cls.agent = LogAnalysisAgent(provider)
        return cls.agent

    @classmethod
    def collect_docker_logs(cls) -> tuple[str, str]:
        """
        Collects logs from Docker containers and writes them to temp files.
        Returns paths to the temporary log files.
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

    @classmethod
    def analyze_and_store(cls, analysis_date: Optional[date] = None) -> LogAnalysis:
        """
        Main method: collect logs, analyze, and store results.

        Args:
            analysis_date: Date for analysis (defaults to today)

        Returns:
            LogAnalysis instance
        """
        if analysis_date is None:
            analysis_date = date.today()

        start_time = time.time()
        backend_log_path = None
        frontend_log_path = None

        try:
            # 1. Collect logs to files
            backend_log_path, frontend_log_path = cls.collect_docker_logs()

            log_size = os.path.getsize(backend_log_path) + os.path.getsize(frontend_log_path)

            if log_size == 0:
                logger.warning("No logs collected from Docker containers")

            # 2. Analyze with LLM (pass file paths)
            agent = cls._get_agent()
            analysis_result = agent.analyze_logs_from_files(backend_log_path, frontend_log_path)

            if not analysis_result:
                raise ValueError("LLM analysis returned empty result")

            # 3. Store in database
            # Ensure findings is a list
            findings = analysis_result.get("key_findings", [])
            if isinstance(findings, str):
                findings = [findings]

            # Create record using helper (idempotent)
            log_analysis = cls._create_or_replace_analysis(
                analysis_date=analysis_date,
                log_size_bytes=log_size,
                summary=analysis_result.get("summary", "No summary provided"),
                severity=analysis_result.get("severity", "INFO"),
                key_findings=findings,
                recommendations=analysis_result.get("recommendations", ""),
                execution_time_seconds=time.time() - start_time,
                gpt_tokens_used=analysis_result.get("gpt_tokens_used", 0),
            )

            # Attach log files
            cls._attach_log_files(log_analysis, backend_log_path, frontend_log_path, analysis_date)

            logger.info(
                "Log analysis complete for %s: record_id=%s, severity=%s",
                analysis_date,
                log_analysis.id,
                log_analysis.severity,
            )
            return log_analysis

        except Exception as e:
            logger.exception("Log analysis failed for date %s", analysis_date)
            # Store error using helper
            log_analysis = cls._create_or_replace_analysis(
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
    def cleanup_old_logs(cls, days_to_keep: int = 30) -> int:
        """
        Deletes log analysis records older than specified days.

        Args:
            days_to_keep: Number of days to retain (default: 30)

        Returns:
            Number of records deleted
        """
        cutoff_date = date.today() - timedelta(days=days_to_keep)

        deleted_count, _ = LogAnalysis.objects.filter(analysis_date__lt=cutoff_date).delete()

        logger.info("Cleaned up %d log analysis records older than %s", deleted_count, cutoff_date)

        return deleted_count

    @classmethod
    def _create_or_replace_analysis(cls, analysis_date: date, **kwargs) -> LogAnalysis:
        """
        Idempotent creation of LogAnalysis record.

        Deletes any existing record for the same date before creating new one.

        Args:
            analysis_date: Date for the analysis
            **kwargs: Fields to pass to LogAnalysis.objects.create()

        Returns:
            LogAnalysis: Created instance
        """
        existing_count = LogAnalysis.objects.filter(analysis_date=analysis_date).count()
        if existing_count > 0:
            logger.info(
                "Replacing %d existing analysis record(s) for %s", existing_count, analysis_date
            )
            LogAnalysis.objects.filter(analysis_date=analysis_date).delete()
        return LogAnalysis.objects.create(analysis_date=analysis_date, **kwargs)

    @classmethod
    def _attach_log_files(
        cls, log_analysis: LogAnalysis, backend_path: str, frontend_path: str, analysis_date: date
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

    @classmethod
    def generate_email_content(cls, log_analysis_id: int) -> tuple[str, str]:
        """Generate email subject and HTML content for log analysis report.

        Fetches the LogAnalysis from database to ensure fresh data and
        decouple from in-memory instances.

        Args:
            log_analysis_id: ID of the LogAnalysis record

        Returns:
            Tuple of (subject, html_content)

        Raises:
            LogAnalysis.DoesNotExist: If the record is not found
        """
        try:
            log_analysis = LogAnalysis.objects.get(id=log_analysis_id)
        except LogAnalysis.DoesNotExist:
            logger.error("LogAnalysis %s not found for email generation", log_analysis_id)
            raise

        subject = f"[{log_analysis.severity}] Daily Log Analysis - {log_analysis.analysis_date}"

        context = {
            "environment": settings.ENVIRONMENT,
            "log_analysis": log_analysis,
            "log_size_kb": f"{log_analysis.log_size_bytes / 1024:.1f}",
            "execution_time": f"{log_analysis.execution_time_seconds:.1f}",
            "admin_domain": settings.ADMIN_DOMAIN,
        }

        html_content = render_to_string("monitoring/email/log_analysis.html", context)

        logger.debug("Generated email content for analysis %s", log_analysis_id)
        return subject, html_content


class LogAnalysisEmailService:
    """
    Handles LogAnalysis-specific email generation and sending.

    This service encapsulates all business logic related to LogAnalysis emails,
    including data fetching, context preparation, and template rendering.
    """

    @classmethod
    def generate_and_send(cls, log_analysis_id: int) -> None:
        """
        Generate LogAnalysis email and send asynchronously.

        Args:
            log_analysis_id: ID of the LogAnalysis record

        Raises:
            LogAnalysis.DoesNotExist: If the record is not found
        """
        try:
            log_analysis = LogAnalysis.objects.get(id=log_analysis_id)
        except LogAnalysis.DoesNotExist:
            logger.error("LogAnalysis %s not found for email generation", log_analysis_id)
            raise

        # Prepare subject
        subject = f"[{log_analysis.severity}] Daily Log Analysis - {log_analysis.analysis_date}"

        # Prepare context
        context = {
            "environment": settings.ENVIRONMENT,
            "log_analysis": log_analysis,
            "log_size_kb": f"{log_analysis.log_size_bytes / 1024:.1f}",
            "execution_time": f"{log_analysis.execution_time_seconds:.1f}",
            "admin_domain": settings.ADMIN_DOMAIN,
        }

        # Render template
        html_content = render_to_string("monitoring/email/log_analysis.html", context)

        logger.info(
            "Sending log analysis email for %s (severity: %s)",
            log_analysis.analysis_date,
            log_analysis.severity,
        )

        # Send via common service
        EmailService.send_async(subject, html_content)
