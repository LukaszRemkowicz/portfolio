from unittest.mock import MagicMock, patch

import pytest

from core.ai_agents import GPTTranslationAgent


@pytest.fixture
def mock_openai_client():
    with patch("core.ai_agents.OpenAI") as mock:
        yield mock


class TestGPTTranslationAgent:
    def test_translate_calls_openai_correctly(self, mock_openai_client):
        """Test that the agent initializes client and calls chat.completions.create"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Przetłumaczony tekst"

        mock_client_instance = mock_openai_client.return_value
        mock_client_instance.chat.completions.create.return_value = mock_response

        # Instantiate agent
        agent = GPTTranslationAgent()

        # Call translate
        result = agent.translate("Hello World", "pl")

        # Assertions
        assert result == "Przetłumaczony tekst"

        # Verify call to OpenAI
        mock_client_instance.chat.completions.create.assert_called_once()
        call_args = mock_client_instance.chat.completions.create.call_args[1]

        assert call_args["model"] == "gpt-4-turbo-preview"
        assert len(call_args["messages"]) == 2
        assert call_args["messages"][0]["role"] == "system"
        assert "Polish" in call_args["messages"][0]["content"]  # Should mention target lang
        assert call_args["messages"][1]["role"] == "user"
        assert call_args["messages"][1]["content"] == "Hello World"

    def test_translate_handles_api_error_gracefully(self, mock_openai_client):
        """Test that the agent returns None or fallback when API fails"""
        mock_client_instance = mock_openai_client.return_value
        # Simulate API Exception
        mock_client_instance.chat.completions.create.side_effect = Exception("API Error")

        agent = GPTTranslationAgent()
        result = agent.translate("Hello", "pl")

        # We decide: Should it return None? Or raise?
        # Plan says "handled by service".
        # Let's say agent return None on failure, so service can stub.
        assert result is None
