from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MonitoringJobName(str, Enum):
    LOG_REPORT = "log_report"
    SITEMAP_REPORT = "sitemap_report"


class ReasoningEffort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def validate_non_empty_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def validate_string_list(values: list[str], field_name: str) -> None:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list of strings")
    if not all(isinstance(item, str) for item in values):
        raise ValueError(f"{field_name} must contain only strings")


@dataclass(frozen=True)
class MonitoringJobDefinition:
    job_name: MonitoringJobName
    prompt_asset: str
    response_schema_asset: str
    description: str

    def __post_init__(self) -> None:
        validate_non_empty_text(self.prompt_asset, "prompt_asset")
        validate_non_empty_text(self.response_schema_asset, "response_schema_asset")
        validate_non_empty_text(self.description, "description")


@dataclass(frozen=True)
class MonitoringJobExecutionContext:
    session_id: str
    job_name: MonitoringJobName
    prompt_version: str

    def __post_init__(self) -> None:
        validate_non_empty_text(self.session_id, "session_id")
        validate_non_empty_text(self.prompt_version, "prompt_version")


@dataclass(frozen=True)
class LLMSummaryResult:
    summary: str
    findings: list[str] = field(default_factory=list)
    reasoning_effort: ReasoningEffort = ReasoningEffort.LOW

    def __post_init__(self) -> None:
        validate_non_empty_text(self.summary, "summary")
        validate_string_list(self.findings, "findings")


@dataclass(frozen=True)
class LLMRunRecord:
    session_id: str
    job_name: MonitoringJobName
    prompt_version: str
    status: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    execution_time_seconds: float = 0.0
    findings_summary: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_non_empty_text(self.session_id, "session_id")
        validate_non_empty_text(self.prompt_version, "prompt_version")
        validate_non_empty_text(self.status, "status")
        validate_string_list(self.findings_summary, "findings_summary")
        if self.tokens_used < 0:
            raise ValueError("tokens_used must be >= 0")
        if self.cost_usd < 0:
            raise ValueError("cost_usd must be >= 0")
        if self.execution_time_seconds < 0:
            raise ValueError("execution_time_seconds must be >= 0")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dict")


@dataclass(frozen=True)
class LogReportResult:
    summary: str
    severity: str
    key_findings: list[str] = field(default_factory=list)
    recommendations: str = ""
    trend_summary: str = ""
    gpt_tokens_used: int = 0
    gpt_cost_usd: float = 0.0

    def __post_init__(self) -> None:
        validate_non_empty_text(self.summary, "summary")
        validate_non_empty_text(self.severity, "severity")
        validate_string_list(self.key_findings, "key_findings")
        validate_non_negative_int(self.gpt_tokens_used, "gpt_tokens_used")
        validate_non_negative_float(self.gpt_cost_usd, "gpt_cost_usd")


def validate_non_negative_int(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0")


def validate_non_negative_float(value: float, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0")
