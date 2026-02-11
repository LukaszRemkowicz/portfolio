import logging
from typing import Optional, cast

from common.llm.protocols import LLMProvider

logger = logging.getLogger(__name__)


class LogAnalysisAgent:
    """
    Agent responsible for analyzing Docker logs using LLM.
    Provider-agnostic design (GPT, Gemini, Claude, etc.).
    """

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def analyze_logs_from_files(
        self, backend_log_path: str, frontend_log_path: str
    ) -> Optional[dict]:
        """
        Analyzes logs from file paths to minimize memory usage.
        Reads only the tail of the files.
        """
        logger.info("Starting log analysis from files with LLM")

        # specific limit for context window
        MAX_CHARS_PER_LOG = 25000

        backend_content = self._read_file_tail(backend_log_path, MAX_CHARS_PER_LOG)
        frontend_content = self._read_file_tail(frontend_log_path, MAX_CHARS_PER_LOG)

        return self.analyze_logs(backend_content, frontend_content)

    def _read_file_tail(self, file_path: str, max_chars: int) -> str:
        """Reads the last max_chars from a file efficiently."""
        import os

        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "r", errors="replace") as f:
                if file_size > max_chars:
                    f.seek(file_size - max_chars)
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read log file {file_path}: {e}")
            return ""

    def analyze_logs(self, backend_logs: str, frontend_logs: str) -> Optional[dict]:
        """
        Analyzes logs and returns structured insights.

        Returns:
            {
                "summary": str,
                "severity": "INFO" | "WARNING" | "CRITICAL",
                "key_findings": [str, ...],
                "recommendations": str
            }
        """
        logger.info("Preparing prompt for LLM")

        prompt = self._build_analysis_prompt()
        combined_logs = self._prepare_logs(backend_logs, frontend_logs)

        logger.info(f"Sending request to LLM provider (prompt size: {len(combined_logs)} chars)")
        result, usage = self.provider.ask_question_with_usage(
            system_prompt=prompt,
            user_message=combined_logs,
            temperature=0.2,
        )

        if result:
            logger.info(f"LLM response received (length: {len(result)})")
            # debug: print first 100 chars to verify content
            logger.info(f"LLM response start: {result[:100]}")

            try:
                parsed = self._parse_response(result)
                # Inject usage stats
                parsed["gpt_tokens_used"] = usage.get("total_tokens", 0)
                logger.info(
                    f"LLM response parsed successfully. Tokens used: {parsed['gpt_tokens_used']}"
                )
                return parsed
            except Exception as e:
                logger.error(f"Error during parsing: {e}")
                raise

        logger.error("LLM log analysis failed: Empty result")
        return None

    def _build_analysis_prompt(self) -> str:
        return """
        You are a DevOps log analysis expert. Analyze the following Docker logs.

        Focus on:
        - Errors and exceptions
        - Performance issues (slow queries, timeouts)
        - Security concerns (failed auth, suspicious requests)
        - Resource usage patterns
        - Unusual patterns or anomalies

        Classify severity:
        - INFO: Normal operation, no issues
        - WARNING: Minor issues, should monitor
        - CRITICAL: Urgent issues requiring immediate attention

        Return JSON:
        {
          "summary": "Brief overview (2-3 sentences)",
          "severity": "INFO|WARNING|CRITICAL",
          "key_findings": ["finding1", "finding2", ...],
          "recommendations": "Actionable next steps"
        }
        """

    def _prepare_logs(self, backend: str, frontend: str) -> str:
        """Truncates and formats logs for GPT (avoid token limits)."""
        MAX_CHARS = 50000  # ~12k tokens

        # Smart truncation: keep recent logs
        backend_truncated = backend[-MAX_CHARS // 2 :] if len(backend) > MAX_CHARS // 2 else backend
        frontend_truncated = (
            frontend[-MAX_CHARS // 2 :] if len(frontend) > MAX_CHARS // 2 else frontend
        )

        return f"""
=== BACKEND LOGS ===
{backend_truncated}

=== FRONTEND LOGS ===
{frontend_truncated}
"""

    def _parse_response(self, response: str) -> dict:
        """Parses GPT JSON response."""
        import json

        try:
            return cast(dict, json.loads(response))
        except json.JSONDecodeError:
            # Extract JSON from markdown code blocks if present
            import re

            try:
                # Use a specific, non-greedy match to avoid potential regex denial of service
                # or memory issues on large strings
                # Limit the search to avoid scanning massive strings if not needed
                match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
                if match:
                    return cast(dict, json.loads(match.group(1)))

                # Fallback: try to find just the first { and last }
                start = response.find("{")
                end = response.rfind("}")
                if start != -1 and end != -1:
                    return cast(dict, json.loads(response[start : end + 1]))

            except Exception as e:
                logger.error(f"Failed to parse JSON with regex/fallback: {e}")
                pass

            logger.warning("Failed to parse JSON, using fallback")
            return {
                "summary": response[:500],
                "severity": "WARNING",
                "key_findings": [],
                "recommendations": "",
            }
