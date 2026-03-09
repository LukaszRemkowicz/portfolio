from monitoring.agent.context import (
    APPLICATION_MONITORING_CONTEXT,
    BOT_DETECTION_CONTEXT,
    HISTORICAL_CONTEXT,
    NORMAL_PATTERNS_CONTEXT,
    OWASP_SECURITY_CONTEXT,
    PROJECT_CONTEXT,
    RECOMMENDATIONS_GUIDE,
    RESPONSE_FORMAT,
    SEVERITY_GUIDE,
)


class TestAgentContext:
    def test_context_constants_exist_and_are_strings(self):
        """Verifies that all prompt context constants exist and are non-empty strings."""
        constants = [
            PROJECT_CONTEXT,
            NORMAL_PATTERNS_CONTEXT,
            APPLICATION_MONITORING_CONTEXT,
            BOT_DETECTION_CONTEXT,
            OWASP_SECURITY_CONTEXT,
            SEVERITY_GUIDE,
            RECOMMENDATIONS_GUIDE,
            RESPONSE_FORMAT,
        ]
        for const in constants:
            assert isinstance(const, str)
            assert len(const) > 50  # Ensure they actually contain content

    def test_owasp_context_mentions_key_vulnerabilities(self):
        """Verifies the OWASP context includes the key vulnerabilities we care about."""
        assert "A01 Broken Access Control" in OWASP_SECURITY_CONTEXT
        assert "A03 Injection" in OWASP_SECURITY_CONTEXT
        assert "A05 Security Misconfiguration" in OWASP_SECURITY_CONTEXT

    def test_bot_detection_context_mentions_timestamps(self):
        """Verifies bot detection instructs the LLM to report timestamps."""
        assert "timestamp" in BOT_DETECTION_CONTEXT.lower()
        assert "LAST probe" in BOT_DETECTION_CONTEXT

    def test_historical_context_exists_and_is_non_empty(self):
        """HISTORICAL_CONTEXT constant is defined and carries substantial content."""
        assert isinstance(HISTORICAL_CONTEXT, str)
        assert len(HISTORICAL_CONTEXT) > 50

    def test_historical_context_mentions_temporal_comparison(self):
        """HISTORICAL_CONTEXT instructs LLM to compare new vs. old data."""
        assert "24h" in HISTORICAL_CONTEXT or "last 24" in HISTORICAL_CONTEXT.lower()

    def test_response_format_includes_trend_summary(self):
        """RESPONSE_FORMAT JSON schema exposes trend_summary field."""
        assert "trend_summary" in RESPONSE_FORMAT
