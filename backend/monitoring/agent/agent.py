import json
import logging
import os
import re
from collections.abc import Mapping
from typing import Optional, cast

from common.llm.protocols import LLMProvider
from monitoring.agent.skills import build_monitoring_system_prompt_with_owasp as build_prompt
from monitoring.log_sources import LOG_SOURCES, REQUIRED_LOG_SOURCE

logger = logging.getLogger(__name__)


LEGACY_LOG_KEYS = ("backend", "frontend", "nginx")


class LogAnalysisAgent:
    """
    Agent responsible for analyzing Docker logs using LLM.
    Provider-agnostic design (GPT, Gemini, Claude, etc.).
    """

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def analyze_logs_from_files(
        self,
        log_paths: Mapping[str, Optional[str]],
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

        rendered_logs = {
            key: self._read_file_tail(path, MAX_CHARS_PER_LOG) if path else ""
            for key, path in log_paths.items()
        }

        return self.analyze_logs(rendered_logs, collected_at, historical_context)

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
        logs_by_key: Mapping[str, str] | str,
        collected_at: str = "",
        historical_context: str = "",
        *legacy_logs: str,
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
        normalized_logs = self._normalize_log_input(
            logs_by_key,
            collected_at=collected_at,
            historical_context=historical_context,
            legacy_logs=legacy_logs,
        )

        logger.info("Preparing prompt for LLM")

        prompt = build_prompt(historical_context=historical_context)
        combined_logs = self._prepare_logs(normalized_logs, collected_at=collected_at)

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

    def _normalize_log_input(
        self,
        logs_by_key: Mapping[str, str] | str,
        *,
        collected_at: str,
        historical_context: str,
        legacy_logs: tuple[str, ...],
    ) -> Mapping[str, str]:
        """Accept both registry-based mappings and the legacy positional API."""
        if isinstance(logs_by_key, Mapping):
            return logs_by_key

        legacy_values = (logs_by_key, collected_at, historical_context, *legacy_logs)
        normalized: dict[str, str] = {}
        for key, value in zip(LEGACY_LOG_KEYS, legacy_values):
            if value:
                normalized[key] = value
        return normalized

    def _prepare_logs(
        self,
        logs_by_key: Mapping[str, str],
        collected_at: str = "",
    ) -> str:
        """Truncates and formats logs for LLM (avoid token limits)."""
        MAX_CHARS = 50000  # ~12k tokens
        active_sources = [source for source in LOG_SOURCES if logs_by_key.get(source.key)]
        if not active_sources:
            return f"Log collection timestamp: {collected_at}\n"

        section_limit = MAX_CHARS // len(active_sources)
        sections = []
        for source in active_sources:
            content = logs_by_key.get(source.key, "")
            truncated = content[-section_limit:] if len(content) > section_limit else content
            sections.append(f"\n        === {source.prompt_section} ===\n        {truncated}\n")

        metadata = f"Log collection timestamp: {collected_at}\n" if collected_at else ""
        if REQUIRED_LOG_SOURCE.key not in logs_by_key:
            logger.warning(
                "Required log source '%s' missing from analysis input", REQUIRED_LOG_SOURCE.key
            )
        return f"{metadata}{''.join(sections)}"

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
