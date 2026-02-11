from unittest.mock import MagicMock

import pytest

from common.llm.protocols import LLMProvider
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
        mock_usage = {"total_tokens": 100}
        mock_llm_provider.ask_question_with_usage.return_value = (mock_response, mock_usage)

        result = agent.analyze_logs("backend logs", "frontend logs")

        assert result is not None
        assert result["summary"] == "Test summary"
        assert result["severity"] == "INFO"
        assert result["gpt_tokens_used"] == 100

        # Verify provider call
        mock_llm_provider.ask_question_with_usage.assert_called_once()
        call_args = mock_llm_provider.ask_question_with_usage.call_args
        assert "backend logs" in call_args.kwargs["user_message"]

    def test_analyze_logs_empty_response(self, agent, mock_llm_provider):
        """Test handling of empty response from LLM."""
        mock_llm_provider.ask_question_with_usage.return_value = (None, {})

        result = agent.analyze_logs("logs", "logs")

        assert result is None

    def test_analyze_logs_json_parsing_fallback(self, agent, mock_llm_provider):
        """Test parsing when response contains markdown code block."""
        mock_response = (
            'Here is the analysis:\n```json\n{"summary": "Markdown summary", '
            '"severity": "WARNING", "key_findings": [], "recommendations": ""}\n```'
        )
        mock_usage = {"total_tokens": 50}
        mock_llm_provider.ask_question_with_usage.return_value = (mock_response, mock_usage)

        result = agent.analyze_logs("logs", "logs")

        assert result is not None
        assert result["summary"] == "Markdown summary"

    def test_analyze_logs_malformed_json(self, agent, mock_llm_provider):
        """Test graceful handling of malformed JSON."""
        mock_response = "Not a JSON response"
        mock_usage = {"total_tokens": 10}
        mock_llm_provider.ask_question_with_usage.return_value = (mock_response, mock_usage)

        # Should return fallback structure
        result = agent.analyze_logs("logs", "logs")

        assert result is not None
        assert result["severity"] == "WARNING"
        assert "Not a JSON response" in result["summary"]
