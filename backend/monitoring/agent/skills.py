"""
Prompt builder functions for the LogAnalysisAgent.

Each function assembles a system prompt from context constants for a specific
analysis scenario. Name the function after what it does, so the caller site
reads like documentation.

Usage:
    from monitoring.agent.skills import build_monitoring_system_prompt_with_owasp

    prompt = build_monitoring_system_prompt_with_owasp()
"""

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


def build_monitoring_system_prompt_with_owasp(historical_context: str = "") -> str:
    """
    Full production prompt: project context + application monitoring + bot detection
    + OWASP security expertise.

    Use for: nightly production log analysis where security awareness is critical.
    Cost: ~2.5k tokens for the system prompt.
    """
    historical_section = (
        HISTORICAL_CONTEXT.format(historical_data=historical_context) if historical_context else ""
    )
    return (
        PROJECT_CONTEXT
        + NORMAL_PATTERNS_CONTEXT
        + APPLICATION_MONITORING_CONTEXT
        + BOT_DETECTION_CONTEXT
        + OWASP_SECURITY_CONTEXT
        + SEVERITY_GUIDE
        + RECOMMENDATIONS_GUIDE
        + historical_section
        + RESPONSE_FORMAT
    )


def build_monitoring_system_prompt_basic(historical_context: str = "") -> str:
    """
    Lightweight prompt: project context + application monitoring only.
    No OWASP security expertise or bot detection.

    Use for: development/test environments, or quick sanity checks where
    security analysis is not needed and cost matters.
    Cost: ~1k tokens for the system prompt.
    """
    historical_section = (
        HISTORICAL_CONTEXT.format(historical_data=historical_context) if historical_context else ""
    )
    return (
        PROJECT_CONTEXT
        + NORMAL_PATTERNS_CONTEXT
        + APPLICATION_MONITORING_CONTEXT
        + SEVERITY_GUIDE
        + RECOMMENDATIONS_GUIDE
        + historical_section
        + RESPONSE_FORMAT
    )
