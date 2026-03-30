from monitoring.monitoring_agent_runner import MonitoringToolExecutor, MonitoringToolLoopRunner
from monitoring.prompt_assets import PromptAssetLoader
from monitoring.types import (
    MonitoringAgentEventType,
    MonitoringJobName,
    MonitoringToolCall,
    MonitoringToolName,
)


class StubProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses: list[str] = responses
        self.calls: list[dict[str, str]] = []

    def ask_question_with_usage(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> tuple[str | None, dict]:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_message": user_message,
                "temperature": str(temperature),
            }
        )
        return self.responses.pop(0), {}

    def ask_question(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.0,
    ) -> str | None:
        response, _usage = self.ask_question_with_usage(system_prompt, user_message, temperature)
        return response


class TestMonitoringToolExecutor:
    def test_prepare_log_report_uses_job_context_payload(self):
        executor = MonitoringToolExecutor(asset_loader=PromptAssetLoader())
        result = executor.execute(
            tool_call=MonitoringToolCall(tool_name=MonitoringToolName.PREPARE_LOG_REPORT),
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={
                "log_report": {
                    "summary": "Healthy",
                    "severity": "INFO",
                }
            },
        )

        assert result.tool_name is MonitoringToolName.PREPARE_LOG_REPORT
        assert result.payload["severity"] == "INFO"


class TestMonitoringToolLoopRunner:
    def test_run_finishes_after_tool_then_final_report(self):
        provider = StubProvider(
            [
                (
                    '{"action":"call_tools","tool_calls":['
                    '{"tool_name":"prepare_log_report","arguments":{}}]}'
                ),
                (
                    '{"action":"final_report","summary":"Healthy","findings":['
                    '"No issues found."]}'
                ),
            ]
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=10)

        result = runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={
                "log_report": {
                    "summary": "Healthy",
                    "severity": "INFO",
                    "key_findings": [],
                }
            },
        )

        assert result.summary == "Healthy"
        assert result.stop_reason == "final_report"
        assert len(result.tool_results) == 1
        assert result.trace[0].event_type is MonitoringAgentEventType.START
        assert result.trace[-1].event_type is MonitoringAgentEventType.STOP
        assert result.tool_results[0].tool_name is MonitoringToolName.PREPARE_LOG_REPORT

    def test_run_supports_multiple_tool_calls_in_one_step(self):
        provider = StubProvider(
            [
                (
                    '{"action":"call_tools","tool_calls":['
                    '{"tool_name":"get_skill_owasp","arguments":{}},'
                    '{"tool_name":"get_skill_response_format","arguments":{}}]}'
                ),
                (
                    '{"action":"final_report","summary":"Security review ready","findings":['
                    '"OWASP guidance loaded.","Response format loaded."]}'
                ),
            ]
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=10)

        result = runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={"log_report": {"summary": "Warning", "severity": "WARNING"}},
        )

        assert len(result.tool_results) == 2
        assert result.tool_results[0].payload["skill_name"] == "owasp_security"
        assert result.tool_results[1].payload["skill_name"] == "response_format"

    def test_run_finishes_immediately_when_no_tools_are_needed(self):
        provider = StubProvider(
            [
                (
                    '{"action":"final_report","summary":"Healthy without tool use","findings":['
                    '"Baseline context was enough."]}'
                )
            ]
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=10)

        result = runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={"log_report": {"summary": "Healthy", "severity": "INFO"}},
        )

        assert result.summary == "Healthy without tool use"
        assert result.tool_results == []
        assert result.iterations == 1

    def test_run_accepts_wrapped_final_report_shape(self):
        provider = StubProvider(
            [
                (
                    '{"final_report":{"severity":"CRITICAL","summary":"Wrapped summary",'
                    '"key_findings":["Wrapped finding"],'
                    '"recommendations":"Fix it.","trend_summary":"Persistent."}}'
                )
            ]
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=10)

        result = runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={"log_report": {"summary": "Warning", "severity": "WARNING"}},
        )

        assert result.stop_reason == "final_report"
        assert result.summary == "Wrapped summary"
        assert result.findings == ["Wrapped finding"]
        assert result.final_payload["severity"] == "CRITICAL"

    def test_run_blocks_duplicate_tool_calls(self):
        provider = StubProvider(
            [
                (
                    '{"action":"call_tools","tool_calls":['
                    '{"tool_name":"get_skill_owasp","arguments":{}}]}'
                ),
                (
                    '{"action":"call_tools","tool_calls":['
                    '{"tool_name":"get_skill_owasp","arguments":{}}]}'
                ),
            ]
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=10)

        result = runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={"log_report": {"summary": "Warning", "severity": "WARNING"}},
        )

        assert result.stop_reason == "duplicate_tool_call"
        assert len(result.tool_results) == 1

    def test_run_stops_at_iteration_limit(self):
        provider = StubProvider(
            [
                (
                    '{"action":"call_tools","tool_calls":['
                    '{"tool_name":"get_skill_owasp","arguments":{"mode":"1"}}]}'
                ),
                (
                    '{"action":"call_tools","tool_calls":['
                    '{"tool_name":"get_skill_owasp","arguments":{"mode":"2"}}]}'
                ),
            ]
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=2)

        result = runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={"log_report": {"summary": "Warning", "severity": "WARNING"}},
        )

        assert result.stop_reason == "max_iterations"
        assert result.iterations == 2

    def test_user_message_includes_tool_docs_but_skill_content_is_on_demand(self):
        provider = StubProvider(
            ['{"action":"final_report","summary":"Ready","findings":[' '"No tools needed."]}']
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=10)

        runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={"log_report": {"summary": "Healthy", "severity": "INFO"}},
        )

        first_message = provider.calls[0]["user_message"]
        assert "get_skill_owasp" in first_message
        assert "Purpose:" in first_message
        assert "OWASP Top 10" not in first_message

    def test_verbose_mode_prints_live_agent_trace(self, capsys):
        provider = StubProvider(
            [
                (
                    '{"action":"call_tools","tool_calls":['
                    '{"tool_name":"prepare_log_report","arguments":{}}]}'
                ),
                (
                    '{"action":"final_report","summary":"Healthy","findings":['
                    '"No issues found."]}'
                ),
            ]
        )
        runner = MonitoringToolLoopRunner(provider=provider, max_iterations=10, verbose=True)

        runner.run(
            job_name=MonitoringJobName.LOG_REPORT,
            job_context={
                "log_report": {
                    "summary": "Healthy",
                    "severity": "INFO",
                }
            },
        )

        captured = capsys.readouterr()
        assert "[monitoring-agent] starting job=log_report" in captured.out
        assert "[monitoring-agent] iteration=1 asking_llm.." in captured.out
        assert "[monitoring-agent] iteration=1 tool=prepare_log_report start.." in captured.out
        assert "[monitoring-agent] stop_reason=final_report" in captured.out
