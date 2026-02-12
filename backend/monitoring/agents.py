import json
import logging
import os
import re
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
        Reads only the tail of the files (defined by MAX_CHARS_PER_LOG) to:
        1. Fit within the LLM context window (token limit).
        2. Capture the most relevant/recent errors.
        3. Control API costs by limiting token usage.
        """
        logger.info("Starting log analysis from files with LLM")

        # specific limit for context window
        # REASONING:
        # 1. AI Context Window: LLMs have token limits (e.g. 128k). Sending 500MB logs will crash
        # the request.
        # 2. Cost: Processing massive files is expensive.
        # 3. Relevance: We care about RECENT errors (at the end of the file), not old history.
        # 25,000 chars is roughly 6-8k tokens, leaving plenty of room for the system prompt.
        MAX_CHARS_PER_LOG = 25000

        backend_content = self._read_file_tail(backend_log_path, MAX_CHARS_PER_LOG)
        frontend_content = self._read_file_tail(frontend_log_path, MAX_CHARS_PER_LOG)

        return self.analyze_logs(backend_content, frontend_content)

    def _read_file_tail(self, file_path: str, max_chars: int) -> str:
        """Reads the last max_chars from a file efficiently."""
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "r", errors="replace") as f:
                if file_size > max_chars:
                    f.seek(file_size - max_chars)
                return f.read()
        except Exception as e:
            logger.error("Failed to read log file %s: %s", file_path, e)
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

        logger.info("Sending request to LLM provider (prompt size: %d chars)", len(combined_logs))
        result, usage = self.provider.ask_question_with_usage(
            system_prompt=prompt,
            user_message=combined_logs,
            temperature=0.2,
        )

        if result:
            logger.info("LLM response received (length: %d)", len(result))
            # debug: print first 100 chars to verify content
            logger.info("LLM response start: %s", result[:100])

            try:
                parsed = self._parse_response(result)
                # Inject usage stats
                parsed["gpt_tokens_used"] = usage.get("total_tokens", 0)
                logger.info(
                    "LLM response parsed successfully. Tokens used: %s", parsed["gpt_tokens_used"]
                )
                return parsed
            except Exception as e:
                logger.error("Error during parsing: %s", e)
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
        """
        Parses GPT JSON response.

        LLMs often return "conversational" text wrapping the JSON
        (e.g., "Here is the JSON: ```json ... ```").
        This method attempts to:
        1. Parse the string directly (if it's pure JSON).
        2. Extract JSON from markdown code blocks using regex.
        3. Fallback to substring extraction if regex fails.
        """
        try:
            return cast(dict, json.loads(response))
        except json.JSONDecodeError:
            # Extract JSON from markdown code blocks if present

            try:
                # Use a specific, non-greedy match to avoid potential regex denial of service
                # or memory issues on large strings
                # Regex Explanation:
                # ```json       -> Matches literal markdown code block start
                # \s*           -> Matches optional whitespace
                # (\{.*?\})     -> Captures the JSON object (non-greedy match between braces)
                # \s*           -> Matches optional whitespace
                # ```           -> Matches literal markdown code block end
                # re.DOTALL     -> Allows '.' to match newlines (JSON is often multi-line)
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
