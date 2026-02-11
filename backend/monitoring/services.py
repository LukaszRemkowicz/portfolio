import logging
import os
import subprocess
import time
from datetime import date, timedelta
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail

from .agents import LogAnalysisAgent
from .models import LogAnalysis

logger = logging.getLogger(__name__)


class LogCollectionService:
    """Service for collecting and analyzing Docker logs."""

    agent: Optional[LogAnalysisAgent] = None

    @classmethod
    def _get_agent(cls) -> LogAnalysisAgent:
        """Lazy-load log analysis agent with configured LLM provider."""
        if cls.agent is None:
            # Import here to avoid circular dependencies if translation app structure changes
            # Import here to avoid circular dependencies if translation app structure changes
            from common.llm.factory import get_llm_provider

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

            # Find docker executable dynamically
            import shutil

            docker_path = shutil.which("docker")

            if not docker_path:
                # Fallback to a common location if not in PATH
                if os.path.exists("/usr/local/bin/docker"):
                    docker_path = "/usr/local/bin/docker"
                elif os.path.exists("/usr/bin/docker"):
                    docker_path = "/usr/bin/docker"
                else:
                    raise FileNotFoundError("Could not find 'docker' executable in PATH")

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

            logger.info(f"Collected logs to files: Backend={be_size}b, Frontend={fe_size}b")

            return backend_log_path, frontend_log_path

        except subprocess.TimeoutExpired:
            logger.error("Docker logs collection timed out")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker command failed: {e}")
            raise

    @classmethod
    def analyze_and_store(cls, analysis_date: Optional[date] = None) -> LogAnalysis:
        """
        Main orchestration method: collect logs, analyze, store, send email.

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

            # 2. Analyze with GPT (pass file paths)
            agent = cls._get_agent()

            # We add a new method to agent to handle file paths
            analysis_result = agent.analyze_logs_from_files(backend_log_path, frontend_log_path)

            if not analysis_result:
                raise ValueError("GPT analysis returned empty result")

            # 3. Store in database
            # Ensure findings is a list
            findings = analysis_result.get("key_findings", [])
            if isinstance(findings, str):
                findings = [findings]

            # Create object first without files
            # Remove any existing record for this date to avoid IntegrityError on retry
            LogAnalysis.objects.filter(analysis_date=analysis_date).delete()

            log_analysis = LogAnalysis.objects.create(
                analysis_date=analysis_date,
                log_size_bytes=log_size,
                summary=analysis_result.get("summary", "No summary provided"),
                severity=analysis_result.get("severity", "INFO"),
                key_findings=findings,
                recommendations=analysis_result.get("recommendations", ""),
                execution_time_seconds=time.time() - start_time,
                gpt_tokens_used=analysis_result.get("gpt_tokens_used", 0),
            )

            # Save files
            from django.core.files import File

            with open(backend_log_path, "rb") as f:
                log_analysis.backend_logs.save(f"backend_{analysis_date}.log", File(f))

            with open(frontend_log_path, "rb") as f:
                log_analysis.frontend_logs.save(f"frontend_{analysis_date}.log", File(f))

            logger.info(f"LogAnalysis record created: {log_analysis.id}")

            # 4. Send email
            cls._send_notification_email(log_analysis)
            log_analysis.email_sent = True
            log_analysis.save(update_fields=["email_sent"])

            logger.info(f"Log analysis complete: {log_analysis.id}")
            return log_analysis

        except Exception as e:
            logger.exception("Log analysis failed")
            # Store error in database but check for existing entry for this date first
            LogAnalysis.objects.filter(analysis_date=analysis_date).delete()

            log_analysis = LogAnalysis.objects.create(
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

        logger.info(f"Cleaned up {deleted_count} log analysis records older than {cutoff_date}")

        return deleted_count

    @classmethod
    def _send_notification_email(cls, log_analysis: LogAnalysis) -> None:
        """Sends email notification with log summary."""
        subject = f"[{log_analysis.severity}] Daily Log Analysis - {log_analysis.analysis_date}"

        # Format key findings
        findings_text = ""
        if log_analysis.key_findings:
            findings_text = "\n".join(f"- {f}" for f in log_analysis.key_findings)
        else:
            findings_text = "No key findings reported."

        message = f"""
Daily Log Analysis Report
=========================

Date: {log_analysis.analysis_date}
Severity: {log_analysis.severity}
Log Size: {log_analysis.log_size_bytes / 1024:.1f} KB
Execution Time: {log_analysis.execution_time_seconds:.1f}s

SUMMARY
-------
{log_analysis.summary}

KEY FINDINGS
------------
{findings_text}

RECOMMENDATIONS
---------------
{log_analysis.recommendations}

---
View full details in Django Admin:
https://{settings.ADMIN_DOMAIN}/admin/monitoring/loganalysis/{log_analysis.id}/
"""

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            logger.info(f"Email sent for log analysis {log_analysis.id}")
        except Exception as e:
            logger.error(f"Failed to send log analysis email: {e}")
            # Don't re-raise, as analysis is already saved
