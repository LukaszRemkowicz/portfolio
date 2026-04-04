from unittest.mock import MagicMock

import pytest

from common.llm.protocols import LLMProvider
from common.llm.providers import MockLLMProvider
from monitoring.agents import LogAnalysisAgent


@pytest.fixture
def mock_llm_provider():
    return MagicMock(spec=LLMProvider)


@pytest.fixture
def agent(mock_llm_provider):
    return LogAnalysisAgent(provider=mock_llm_provider)


class TestLogAnalysisAgent:
    def test_analyze_logs_success(self, agent, mock_llm_provider):
        """Test successful log analysis with valid JSON response."""
        # Mock LLM response
        mock_response = (
            '{"summary": "Test summary", "severity": "INFO", '
            '"key_findings": [], "recommendations": ""}'
        )
        mock_usage = {"total_tokens": 100, "cost_usd": 0.005}
        mock_llm_provider.ask_question_with_usage.return_value = (mock_response, mock_usage)

        result = agent.analyze_logs({"backend": "backend logs"})

        assert result is not None
        assert result["summary"] == "Test summary"
        assert result["severity"] == "INFO"
        assert result["gpt_tokens_used"] == 100
        assert result["gpt_cost_usd"] == 0.005

        # Verify provider call
        mock_llm_provider.ask_question_with_usage.assert_called_once()
        call_args = mock_llm_provider.ask_question_with_usage.call_args
        assert "backend logs" in call_args.kwargs["user_message"]

    def test_analyze_logs_empty_response(self, agent, mock_llm_provider):
        """Test handling of empty response from LLM."""
        mock_llm_provider.ask_question_with_usage.return_value = (None, {})

        result = agent.analyze_logs({"backend": "logs", "nginx_access": "logs"})

        assert result is None

    def test_analyze_logs_json_parsing_fallback(self, agent, mock_llm_provider):
        """Test parsing when response contains markdown code block."""
        mock_response = (
            'Here is the analysis:\n```json\n{"summary": "Markdown summary", '
            '"severity": "WARNING", "key_findings": [], "recommendations": ""}\n```'
        )
        mock_usage = {"total_tokens": 50, "cost_usd": 0.002}
        mock_llm_provider.ask_question_with_usage.return_value = (mock_response, mock_usage)

        result = agent.analyze_logs({"backend": "logs", "nginx_access": "logs"})

        assert result is not None
        assert result["summary"] == "Markdown summary"

    def test_analyze_logs_malformed_json(self, agent, mock_llm_provider):
        """Test graceful handling of malformed JSON."""
        mock_response = "Not a JSON response"
        mock_usage = {"total_tokens": 10, "cost_usd": 0.001}
        mock_llm_provider.ask_question_with_usage.return_value = (mock_response, mock_usage)

        # Should return fallback structure
        result = agent.analyze_logs({"backend": "logs", "nginx_access": "logs"})

        assert result is not None
        assert result["severity"] == "WARNING"
        assert "Not a JSON response" in result["summary"]

    def test_analyze_logs_with_custom_mock_json_path(self):
        """Test the agent using the real MockLLMProvider configured with a specific JSON file."""
        # Create a real MockLLMProvider, not a MagicMock
        provider = MockLLMProvider()
        # Point it to our new attack response fixture
        provider.configure(mock_json_path="monitoring/tests/llm_responses/attack.json")

        agent = LogAnalysisAgent(provider=provider)
        result = agent.analyze_logs({"backend": "dummy logs", "nginx_access": "dummy logs"})

        assert result is not None
        assert result["severity"] == "CRITICAL"
        assert "A05 Security Misconfiguration" in result["key_findings"][0]
        assert result["gpt_tokens_used"] == 600  # Default fallback logic from MockLLMProvider

    def test_analyze_logs_historical_context_in_system_prompt(self, agent, mock_llm_provider):
        """historical_context is injected into the system prompt sent to the LLM."""
        mock_response = (
            '{"summary": "Calm", "severity": "INFO", '
            '"key_findings": [], "recommendations": "", "trend_summary": "Attack calmed down"}'
        )
        mock_llm_provider.ask_question_with_usage.return_value = (mock_response, {})

        historical = "## 2026-03-08 — Severity: CRITICAL\nSummary: Bot attack"
        agent.analyze_logs(
            {"backend": "backend", "frontend": "frontend"},
            historical_context=historical,
        )

        call_kwargs = mock_llm_provider.ask_question_with_usage.call_args.kwargs
        assert historical in call_kwargs["system_prompt"]
