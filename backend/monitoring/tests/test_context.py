from monitoring.agent.context import (
    APPLICATION_MONITORING_CONTEXT,
    BOT_DETECTION_CONTEXT,
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
