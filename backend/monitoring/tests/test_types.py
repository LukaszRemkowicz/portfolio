import pytest

from monitoring.types import (
    LLMRunRecord,
    LLMSummaryResult,
    LogReportResult,
    MonitoringJobDefinition,
    MonitoringJobExecutionContext,
    MonitoringJobName,
    ReasoningEffort,
)


class TestMonitoringTypes:
    def test_monitoring_job_definition_accepts_valid_values(self):
        definition = MonitoringJobDefinition(
            job_name=MonitoringJobName.LOG_REPORT,
            prompt_asset="prompts/monitoring_log_summary.md",
            response_schema_asset="schemas/log_report.schema.json",
            description="Summarize deterministic log findings.",
        )

        assert definition.job_name is MonitoringJobName.LOG_REPORT

    def test_monitoring_job_execution_context_requires_session_id(self):
        with pytest.raises(ValueError, match="session_id must be a non-empty string"):
            MonitoringJobExecutionContext(
                session_id="",
                job_name=MonitoringJobName.SITEMAP_REPORT,
                prompt_version="v1",
            )

    def test_llm_summary_result_validates_findings_type(self):
        with pytest.raises(ValueError, match="findings must contain only strings"):
            LLMSummaryResult(summary="Valid", findings=["ok", 1])  # type: ignore[list-item]

    def test_llm_run_record_validates_numeric_ranges(self):
        with pytest.raises(ValueError, match="tokens_used must be >= 0"):
            LLMRunRecord(
                session_id="session-1",
                job_name=MonitoringJobName.LOG_REPORT,
                prompt_version="v1",
                status="success",
                tokens_used=-1,
            )

    def test_llm_run_record_accepts_valid_values(self):
        record = LLMRunRecord(
            session_id="session-1",
            job_name=MonitoringJobName.SITEMAP_REPORT,
            prompt_version="v1",
            status="success",
            tokens_used=42,
            cost_usd=0.003,
            execution_time_seconds=1.5,
            findings_summary=["Found two redirects."],
            metadata={"source": "test"},
        )

        assert record.job_name is MonitoringJobName.SITEMAP_REPORT
        assert record.findings_summary == ["Found two redirects."]

    def test_llm_summary_result_defaults_reasoning_effort(self):
        result = LLMSummaryResult(summary="Healthy", findings=["No issues found."])

        assert result.reasoning_effort is ReasoningEffort.LOW

    def test_log_report_result_normalizes_valid_contract(self):
        result = LogReportResult(
            summary="Healthy",
            severity="INFO",
            key_findings=["No anomalies"],
            recommendations="No action needed.",
            trend_summary="Stable versus yesterday.",
            gpt_tokens_used=100,
            gpt_cost_usd=0.005,
        )

        assert result.severity == "INFO"
        assert result.key_findings == ["No anomalies"]
