import json
import logging
import os
import re
from typing import Optional, cast

from common.llm.protocols import LLMProvider
from monitoring.agent.skills import build_monitoring_system_prompt_with_owasp as build_prompt

logger = logging.getLogger(__name__)


class LogAnalysisAgent:
    """
    Agent responsible for analyzing Docker logs using LLM.
    Provider-agnostic design (GPT, Gemini, Claude, etc.).
    """

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def analyze_logs_from_files(
        self,
        backend_log_path: str,
        frontend_log_path: str,
        nginx_log_path: Optional[str] = None,
        collected_at: str = "",
        historical_context: str = "",
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
        nginx_content = (
            self._read_file_tail(nginx_log_path, MAX_CHARS_PER_LOG) if nginx_log_path else ""
        )

        return self.analyze_logs(
            backend_content, frontend_content, nginx_content, collected_at, historical_context
        )

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

    def analyze_logs(
        self,
        backend_logs: str,
        frontend_logs: str,
        nginx_logs: str = "",
        collected_at: str = "",
        historical_context: str = "",
    ) -> Optional[dict]:
        """
        Analyzes logs and returns structured insights.

        Returns:
            {
                "summary": str,
                "severity": "INFO" | "WARNING" | "CRITICAL",
                "key_findings": [str, ...],
                "recommendations": str,
                "trend_summary": str,
            }
        """
        logger.info("Preparing prompt for LLM")

        prompt = build_prompt(historical_context=historical_context)
        combined_logs = self._prepare_logs(backend_logs, frontend_logs, nginx_logs, collected_at)

        logger.info("Sending request to LLM provider (prompt size: %d chars)", len(combined_logs))
        result, usage = self.provider.ask_question_with_usage(
            system_prompt=prompt,
            user_message=combined_logs,
            temperature=0.2,
        )

        if result:
            logger.info("LLM response received (length: %d)", len(result))
            logger.info("LLM response start: %s", result[:100])

            try:
                parsed = self._parse_response(result)
                parsed["gpt_tokens_used"] = usage.get("total_tokens", 0)
                parsed["gpt_cost_usd"] = usage.get("cost_usd", 0.0)
                logger.info(
                    "LLM response parsed successfully. Tokens used: %s, cost: $%.6f",
                    parsed["gpt_tokens_used"],
                    parsed["gpt_cost_usd"],
                )
                return parsed
            except Exception as e:
                logger.error("Error during parsing: %s", e)
                raise

        logger.error("LLM log analysis failed: Empty result")
        return None

    def _prepare_logs(
        self,
        backend: str,
        frontend: str,
        nginx: str = "",
        collected_at: str = "",
    ) -> str:
        """Truncates and formats logs for LLM (avoid token limits)."""
        MAX_CHARS = 50000  # ~12k tokens

        # Smart truncation: keep recent logs
        backend_truncated = backend[-MAX_CHARS // 3 :] if len(backend) > MAX_CHARS // 3 else backend
        frontend_truncated = (
            frontend[-MAX_CHARS // 3 :] if len(frontend) > MAX_CHARS // 3 else frontend
        )
        nginx_truncated = nginx[-MAX_CHARS // 3 :] if len(nginx) > MAX_CHARS // 3 else nginx

        nginx_section = (
            f"\n        === NGINX LOGS ===\n        {nginx_truncated}\n" if nginx_truncated else ""
        )

        metadata = f"Log collection timestamp: {collected_at}\n" if collected_at else ""

        return (
            f"{metadata}"
            f"\n        === BACKEND LOGS ===\n        {backend_truncated}"
            f"\n        === FRONTEND LOGS ===\n        {frontend_truncated}"
            f"{nginx_section}"
        )

    def _parse_response(self, response: str) -> dict:
        """
        Parses LLM JSON response.

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
            try:
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

            logger.warning("Failed to parse JSON, using fallback")
            return {
                "summary": response[:500],
                "severity": "WARNING",
                "key_findings": [],
                "recommendations": "",
            }
