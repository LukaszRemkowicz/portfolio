import json
from pathlib import Path

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
        gpt_cost_usd=0.0075,
        key_findings=["Database latency normal", "Cache hit rate high"],
        recommendations="No action needed.\nMonitor disk usage.",
        email_sent=False,
    )


@pytest.fixture
def mock_llm_response():
    """Load mock response from JSON file."""

    json_path = Path(__file__).parent / "llm_responses" / "default.json"
    with open(json_path) as f:
        data = json.load(f)
        data["gpt_tokens_used"] = 150
        data["gpt_cost_usd"] = 0.0075
        return data
