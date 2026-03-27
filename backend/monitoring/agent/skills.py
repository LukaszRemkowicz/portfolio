"""Prompt builder functions for the LogAnalysisAgent."""

from collections.abc import Sequence

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

BASE_MONITORING_SKILLS: tuple[str, ...] = (
    PROJECT_CONTEXT,
    NORMAL_PATTERNS_CONTEXT,
    APPLICATION_MONITORING_CONTEXT,
    SEVERITY_GUIDE,
    RECOMMENDATIONS_GUIDE,
)

SECURITY_MONITORING_SKILLS: tuple[str, ...] = (
    BOT_DETECTION_CONTEXT,
    OWASP_SECURITY_CONTEXT,
)


def _compose_monitoring_prompt(
    sections: Sequence[str],
    historical_context: str = "",
) -> str:
    historical_section: str = (
        HISTORICAL_CONTEXT.format(historical_data=historical_context) if historical_context else ""
    )
    ordered_sections: list[str] = [*sections]
    if historical_section:
        ordered_sections.append(historical_section)
    ordered_sections.append(RESPONSE_FORMAT)
    return "\n\n".join(section.strip() for section in ordered_sections if section.strip())


def build_monitoring_system_prompt_with_owasp(historical_context: str = "") -> str:
    return _compose_monitoring_prompt(
        (
            *BASE_MONITORING_SKILLS,
            *SECURITY_MONITORING_SKILLS,
        ),
        historical_context=historical_context,
    )


def build_monitoring_system_prompt_basic(historical_context: str = "") -> str:
    return _compose_monitoring_prompt(BASE_MONITORING_SKILLS, historical_context=historical_context)
