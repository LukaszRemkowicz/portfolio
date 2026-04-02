from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypedDict

type MonitoringFindingsValue = list[str] | str
type JSONValue = str | int | float | bool | None | JSONObject | JSONArray
type JSONObject = dict[str, JSONValue]
type JSONArray = list[JSONValue]
type RawCollectedLogPaths = dict[str, str | None] | tuple[str | None, ...]


class LogAnalysisPayload(TypedDict, total=False):
    summary: str
    severity: str
    key_findings: MonitoringFindingsValue
    recommendations: str
    trend_summary: str
    gpt_tokens_used: int
    gpt_cost_usd: float


@dataclass(frozen=True)
class HTTPResponseData:
    status_code: int
    text: str
    url: str
    headers: dict[str, str]


class MonitoringJobName(StrEnum):
    LOG_REPORT = "log_report"
    SITEMAP_REPORT = "sitemap_report"


class MonitoringToolName(StrEnum):
    PREPARE_LOG_REPORT = "prepare_log_report"
    GET_SKILL_OWASP = "get_skill_owasp"
    GET_SKILL_RESPONSE_FORMAT = "get_skill_response_format"
    GET_SKILL_BOT_DETECTION = "get_skill_bot_detection"


class ReasoningEffort(StrEnum):
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


def validate_non_negative_int(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0")


def validate_non_negative_float(value: float, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0")


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
class MonitoringToolDefinition:
    tool_name: MonitoringToolName
    description: str
    documentation_asset: str
    when_to_use: list[str] = field(default_factory=list)
    when_not_to_use: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_non_empty_text(self.description, "description")
        validate_non_empty_text(self.documentation_asset, "documentation_asset")
        validate_string_list(self.when_to_use, "when_to_use")
        validate_string_list(self.when_not_to_use, "when_not_to_use")


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
    metadata: JSONObject = field(default_factory=dict)

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


class MonitoringToolDecisionAction(StrEnum):
    CALL_TOOLS = "call_tools"
    FINAL_REPORT = "final_report"


class MonitoringAgentEventType(StrEnum):
    START = "start"
    ITERATION = "iteration"
    ASKING_LLM = "asking_llm"
    DECISION = "decision"
    TOOL_START = "tool_start"
    TOOL_DONE = "tool_done"
    TOOL_SKIPPED = "tool_skipped"
    STOP = "stop"


@dataclass(frozen=True)
class MonitoringAgentTraceEvent:
    event_type: MonitoringAgentEventType
    message: str
    iteration: int | None = None
    tool_name: MonitoringToolName | None = None
    decision_action: MonitoringToolDecisionAction | None = None

    def __post_init__(self) -> None:
        validate_non_empty_text(self.message, "message")
        if self.iteration is not None:
            validate_non_negative_int(self.iteration, "iteration")


@dataclass(frozen=True)
class MonitoringToolCall:
    tool_name: MonitoringToolName
    arguments: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.arguments, dict):
            raise ValueError("arguments must be a dict")
        for key, value in self.arguments.items():
            validate_non_empty_text(key, "arguments key")
            if not isinstance(value, str):
                raise ValueError("arguments values must contain only strings")


@dataclass(frozen=True)
class MonitoringToolDecision:
    action: MonitoringToolDecisionAction
    tool_calls: list[MonitoringToolCall] = field(default_factory=list)
    summary: str = ""
    findings: list[str] = field(default_factory=list)
    payload: JSONObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.tool_calls, list):
            raise ValueError("tool_calls must be a list")
        for tool_call in self.tool_calls:
            if not isinstance(tool_call, MonitoringToolCall):
                raise ValueError("tool_calls must contain only MonitoringToolCall objects")
        validate_string_list(self.findings, "findings")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")
        if self.action is MonitoringToolDecisionAction.CALL_TOOLS:
            if not self.tool_calls:
                raise ValueError("tool_calls action requires at least one tool call")
            if self.summary:
                raise ValueError("tool_calls action cannot include summary")
            if self.payload:
                raise ValueError("tool_calls action cannot include payload")
        if self.action is MonitoringToolDecisionAction.FINAL_REPORT:
            validate_non_empty_text(self.summary, "summary")


@dataclass(frozen=True)
class MonitoringToolResult:
    tool_name: MonitoringToolName
    payload: JSONObject

    def __post_init__(self) -> None:
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")


@dataclass(frozen=True)
class MonitoringToolLoopResult:
    summary: str
    findings: list[str]
    tool_results: list[MonitoringToolResult] = field(default_factory=list)
    trace: list[MonitoringAgentTraceEvent] = field(default_factory=list)
    final_payload: JSONObject = field(default_factory=dict)
    iterations: int = 0
    stop_reason: str = ""

    def __post_init__(self) -> None:
        validate_non_empty_text(self.summary, "summary")
        validate_string_list(self.findings, "findings")
        validate_non_negative_int(self.iterations, "iterations")
        validate_non_empty_text(self.stop_reason, "stop_reason")
        if not isinstance(self.final_payload, dict):
            raise ValueError("final_payload must be a dict")
        if not isinstance(self.tool_results, list):
            raise ValueError("tool_results must be a list")
        for tool_result in self.tool_results:
            if not isinstance(tool_result, MonitoringToolResult):
                raise ValueError("tool_results must contain only MonitoringToolResult objects")
        if not isinstance(self.trace, list):
            raise ValueError("trace must be a list")
        for trace_event in self.trace:
            if not isinstance(trace_event, MonitoringAgentTraceEvent):
                raise ValueError("trace must contain only MonitoringAgentTraceEvent objects")


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

    def to_payload(self) -> JSONObject:
        return {
            "summary": self.summary,
            "severity": self.severity,
            "key_findings": list(self.key_findings),
            "recommendations": self.recommendations,
            "trend_summary": self.trend_summary,
            "gpt_tokens_used": self.gpt_tokens_used,
            "gpt_cost_usd": self.gpt_cost_usd,
        }


class SitemapIssueCategory(StrEnum):
    BROKEN_URL = "broken_url"
    REDIRECT_IN_SITEMAP = "redirect_in_sitemap"
    FINAL_URL_MISMATCH = "final_url_mismatch"
    DUPLICATE_URL = "duplicate_url"
    NON_PROD_DOMAIN = "non_prod_domain"
    FETCH_ERROR = "fetch_error"
    CANONICAL_MISMATCH = "canonical_mismatch"
    NOINDEX_PAGE = "noindex_page"


@dataclass(frozen=True)
class SitemapIssue:
    url: str
    category: SitemapIssueCategory
    message: str
    status_code: int | None = None
    final_url: str | None = None

    def __post_init__(self) -> None:
        validate_non_empty_text(self.url, "url")
        validate_non_empty_text(self.message, "message")
        if self.status_code is not None:
            validate_non_negative_int(self.status_code, "status_code")
        if self.final_url is not None:
            validate_non_empty_text(self.final_url, "final_url")


@dataclass(frozen=True)
class SitemapReportResult:
    root_sitemap_url: str
    total_sitemaps: int
    total_urls: int
    issues: list[SitemapIssue] = field(default_factory=list)

    def __post_init__(self) -> None:
        validate_non_empty_text(self.root_sitemap_url, "root_sitemap_url")
        validate_non_negative_int(self.total_sitemaps, "total_sitemaps")
        validate_non_negative_int(self.total_urls, "total_urls")
        if not isinstance(self.issues, list):
            raise ValueError("issues must be a list")
        for issue in self.issues:
            if not isinstance(issue, SitemapIssue):
                raise ValueError("issues must contain only SitemapIssue objects")


@dataclass(frozen=True)
class SitemapSummaryResult:
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
