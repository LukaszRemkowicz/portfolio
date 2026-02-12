import pytest

from monitoring.tests.factories import LogAnalysisFactory


@pytest.fixture
def log_analysis():
    return LogAnalysisFactory.create(
        summary="System is healthy.",
        severity="INFO",
        log_size_bytes=1024,
        execution_time_seconds=5.5,
        gpt_tokens_used=150,
        key_findings=["Database latency normal", "Cache hit rate high"],
        recommendations="No action needed.\nMonitor disk usage.",
        email_sent=False,
    )


@pytest.fixture
def mock_llm_response():
    """Load mock response from JSON file."""
    import json
    from pathlib import Path

    json_path = Path(__file__).parent / "llm_mock_response.json"
    with open(json_path, "r") as f:
        return json.load(f)
