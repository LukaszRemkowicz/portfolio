from monitoring.agent.skills import (
    build_monitoring_system_prompt_basic,
    build_monitoring_system_prompt_with_owasp,
)


class TestAgentSkills:
    def test_build_monitoring_system_prompt_with_owasp(self):
        """Verifies the full OWASP prompt builder assembles all required pieces."""
        prompt = build_monitoring_system_prompt_with_owasp()

        # Should contain project info
        assert "portfolio website" in prompt
        # Should contain OWASP
        assert "OWASP Top 10" in prompt
        # Should contain Bot Detection
        assert "BOT / ATTACK DETECTION" in prompt

    def test_build_monitoring_system_prompt_basic(self):
        """Verifies the basic prompt builder omits expensive security contexts."""
        prompt = build_monitoring_system_prompt_basic()

        # Should contain project info
        assert "portfolio website" in prompt
        # Should NOT contain OWASP
        assert "OWASP Top 10" not in prompt
        # Should NOT contain Bot Detection
        assert "BOT / ATTACK DETECTION" not in prompt

    def test_owasp_prompt_is_larger_than_basic(self):
        """Verifies the OWASP prompt actually includes more content than the basic one."""
        owasp_prompt = build_monitoring_system_prompt_with_owasp()
        basic_prompt = build_monitoring_system_prompt_basic()

        assert len(owasp_prompt) > len(basic_prompt)
