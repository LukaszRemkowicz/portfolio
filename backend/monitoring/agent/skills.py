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
    NORMAL_PATTERNS_CONTEXT,
    OWASP_SECURITY_CONTEXT,
    PROJECT_CONTEXT,
    RECOMMENDATIONS_GUIDE,
    RESPONSE_FORMAT,
    SEVERITY_GUIDE,
)


def build_monitoring_system_prompt_with_owasp() -> str:
    """
    Full production prompt: project context + application monitoring + bot detection
    + OWASP security expertise.

    Use for: nightly production log analysis where security awareness is critical.
    Cost: ~2.5k tokens for the system prompt.
    """
    return (
        PROJECT_CONTEXT
        + NORMAL_PATTERNS_CONTEXT
        + APPLICATION_MONITORING_CONTEXT
        + BOT_DETECTION_CONTEXT
        + OWASP_SECURITY_CONTEXT
        + SEVERITY_GUIDE
        + RECOMMENDATIONS_GUIDE
        + RESPONSE_FORMAT
    )


def build_monitoring_system_prompt_basic() -> str:
    """
    Lightweight prompt: project context + application monitoring only.
    No OWASP security expertise or bot detection.

    Use for: development/test environments, or quick sanity checks where
    security analysis is not needed and cost matters.
    Cost: ~1k tokens for the system prompt.
    """
    return (
        PROJECT_CONTEXT
        + NORMAL_PATTERNS_CONTEXT
        + APPLICATION_MONITORING_CONTEXT
        + SEVERITY_GUIDE
        + RECOMMENDATIONS_GUIDE
        + RESPONSE_FORMAT
    )
