from unittest.mock import MagicMock, patch

import pytest

from core.agents import GPTTranslationAgent


@pytest.fixture
def mock_openai_client():
    with patch("core.agents.OpenAI") as mock:
        yield mock


class TestGPTTranslationAgent:
    def test_translate_calls_openai_correctly(self, mock_openai_client):
        """Test that the agent initializes client and calls chat.completions.create twice"""
        # Setup mock responses
        mock_response1 = MagicMock()
        mock_response1.choices[0].message.content = "Translated raw"
        
        mock_response2 = MagicMock()
        mock_response2.choices[0].message.content = "Przetłumaczony tekst"

        mock_client_instance = mock_openai_client.return_value
        mock_client_instance.chat.completions.create.side_effect = [mock_response1, mock_response2]

        # Instantiate agent
        agent = GPTTranslationAgent()

        # Call translate
        result = agent.translate("Hello World", "pl")

        # Assertions
        assert result == "Przetłumaczony tekst"

        # Verify calls to OpenAI
        assert mock_client_instance.chat.completions.create.call_count == 2
        
        # 1st call (Translate)
        call1 = mock_client_instance.chat.completions.create.call_args_list[0][1]
        assert call1["model"] == "gpt-4o"
        assert "Polish" in call1["messages"][0]["content"]
        assert call1["messages"][1]["content"] == "Hello World"

        # 2nd call (Edit)
        call2 = mock_client_instance.chat.completions.create.call_args_list[1][1]
        assert call2["model"] == "gpt-4o"
        assert "Polish" in call2["messages"][0]["content"]
        assert call2["messages"][1]["content"] == "Translated raw"

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
