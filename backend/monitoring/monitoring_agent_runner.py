"""Bounded monitoring-agent runtime for app-level LLM tool execution.

This module provides the small constrained agent loop used by the monitoring
system. It is intentionally narrow:

- code decides the job scope before the runtime starts
- the LLM can only use documented app-level tools
- tools return deterministic data or skill fragments
- the runtime stops on a final report or the iteration limit

It is designed to be testable in isolation before being wired into scheduled
Celery monitoring jobs.
"""

import json
import logging
import re
from collections.abc import Mapping

from common.llm.protocols import LLMProvider

from .prompt_assets import PromptAssetLoader
from .types import (
    JSONArray,
    JSONObject,
    JSONValue,
    MonitoringAgentEventType,
    MonitoringAgentTraceEvent,
    MonitoringJobName,
    MonitoringToolCall,
    MonitoringToolDecision,
    MonitoringToolDecisionAction,
    MonitoringToolDefinition,
    MonitoringToolLoopResult,
    MonitoringToolName,
    MonitoringToolResult,
)

logger = logging.getLogger(__name__)


class MonitoringToolRegistry:
    """Registry of app-level tools exposed to the monitoring agent.

    This registry is the policy boundary for tool availability inside the
    monitoring runtime. The LLM never discovers tools dynamically and never
    receives direct execution access to arbitrary Python functions. Instead,
    the runtime serializes only the definitions returned here.

    Each definition should describe:
    - what the tool does
    - when it should be used
    - when it should not be used
    - which documentation asset explains the tool contract

    In practice this means the registry acts as the curated tool menu for the
    monitoring agent. Adding a tool here is an explicit product and safety
    decision, not just an implementation detail.
    """

    @staticmethod
    def get_definitions() -> list[MonitoringToolDefinition]:
        """Return the tool definitions exposed to the LLM for a monitoring run.

        The returned list is embedded into the user message for each loop
        iteration, so the LLM can decide whether it needs additional data or a
        skill fragment before producing the final report.
        """
        return [
            MonitoringToolDefinition(
                tool_name=MonitoringToolName.PREPARE_LOG_REPORT,
                description="Return the prepared structured log report for the current job.",
                documentation_asset="tools/prepare_log_report.md",
                when_to_use=[
                    "You need the current log findings for the monitoring job.",
                    "The log report has not been retrieved yet in this loop.",
                ],
                when_not_to_use=[
                    "The current job is not log monitoring.",
                    "The same log report was already returned without new context.",
                ],
            ),
            MonitoringToolDefinition(
                tool_name=MonitoringToolName.GET_SKILL_OWASP,
                description="Return OWASP-oriented security analysis guidance.",
                documentation_asset="tools/get_skill_owasp.md",
                when_to_use=[
                    "Logs suggest probing, abuse, injection, or auth attacks.",
                ],
                when_not_to_use=[
                    "The findings are routine and do not need security interpretation.",
                ],
            ),
            MonitoringToolDefinition(
                tool_name=MonitoringToolName.GET_SKILL_RESPONSE_FORMAT,
                description="Return the required final response format guidance.",
                documentation_asset="tools/get_skill_response_format.md",
                when_to_use=[
                    "You need the exact output contract before returning the final report.",
                ],
                when_not_to_use=[
                    "You already know the response contract in this loop.",
                ],
            ),
            MonitoringToolDefinition(
                tool_name=MonitoringToolName.GET_SKILL_BOT_DETECTION,
                description="Return bot and scanner detection guidance for suspicious traffic.",
                documentation_asset="tools/get_skill_bot_detection.md",
                when_to_use=[
                    "Logs show suspicious traffic patterns or probe clusters.",
                ],
                when_not_to_use=[
                    "The findings are ordinary app errors with no suspicious traffic.",
                ],
            ),
        ]


class MonitoringToolExecutor:
    """Execute a single app-level monitoring tool selected by the LLM.

    This executor is deliberately small and deterministic. It never exposes
    arbitrary shell, filesystem, or network access to the model. Instead, each
    supported tool is mapped to a narrow Python implementation.
    """

    def __init__(self, asset_loader: PromptAssetLoader | None = None) -> None:
        resolved_loader: PromptAssetLoader = asset_loader or PromptAssetLoader()
        self.asset_loader: PromptAssetLoader = resolved_loader

    def execute(
        self,
        tool_call: MonitoringToolCall,
        job_name: MonitoringJobName,
        job_context: Mapping[str, JSONValue],
    ) -> MonitoringToolResult:
        """Execute a single tool request and return its structured payload.

        Args:
            tool_call: Parsed LLM request describing which tool to run.
            job_name: The already-approved job scope for this runtime.
            job_context: Deterministic context prepared by application code.

        Returns:
            A `MonitoringToolResult` containing the tool name and payload.

        Raises:
            ValueError: If the tool is unsupported or incompatible with the
                current job scope.
        """
        logger.info(
            "Executing monitoring tool: tool=%s job=%s",
            tool_call.tool_name.value,
            job_name.value,
        )
        logger.debug(
            "Monitoring tool arguments: tool=%s arguments=%s",
            tool_call.tool_name.value,
            tool_call.arguments,
        )
        if tool_call.tool_name is MonitoringToolName.PREPARE_LOG_REPORT:
            return self._prepare_log_report(job_name, job_context)
        if tool_call.tool_name is MonitoringToolName.GET_SKILL_OWASP:
            return self._load_skill(
                tool_name=tool_call.tool_name,
                skill_name="owasp_security",
                asset_path="skills/owasp_security.md",
            )
        if tool_call.tool_name is MonitoringToolName.GET_SKILL_RESPONSE_FORMAT:
            return self._load_skill(
                tool_name=tool_call.tool_name,
                skill_name="response_format",
                asset_path="prompts/monitoring_log_response_format.md",
            )
        if tool_call.tool_name is MonitoringToolName.GET_SKILL_BOT_DETECTION:
            return self._load_skill(
                tool_name=tool_call.tool_name,
                skill_name="bot_detection",
                asset_path="skills/bot_detection.md",
            )
        raise ValueError(f"Unsupported monitoring tool: {tool_call.tool_name.value}")

    def _prepare_log_report(
        self,
        job_name: MonitoringJobName,
        job_context: Mapping[str, JSONValue],
    ) -> MonitoringToolResult:
        """Return the prepared deterministic log report for a log-monitoring job."""
        if job_name is not MonitoringJobName.LOG_REPORT:
            raise ValueError("prepare_log_report can only be used for log monitoring jobs")

        log_report: JSONValue | None = job_context.get("log_report")
        if not isinstance(log_report, dict):
            raise ValueError("job_context must include a dict log_report for prepare_log_report")

        return MonitoringToolResult(
            tool_name=MonitoringToolName.PREPARE_LOG_REPORT,
            payload=log_report,
        )

    def _load_skill(
        self,
        *,
        tool_name: MonitoringToolName,
        skill_name: str,
        asset_path: str,
    ) -> MonitoringToolResult:
        """Load a single skill fragment on demand from the prompt asset bundle."""
        content: str = self.asset_loader.load_text(asset_path)
        logger.debug(
            "Loaded monitoring skill asset: tool=%s skill=%s chars=%d",
            tool_name.value,
            skill_name,
            len(content),
        )
        return MonitoringToolResult(
            tool_name=tool_name,
            payload={
                "skill_name": skill_name,
                "content": content,
            },
        )


class MonitoringToolLoopRunner:
    """Run the bounded monitoring-agent loop for a single scheduled job.

    The runtime asks the LLM to either:
    - request one or more tools, or
    - return the final report

    Duplicate tool calls with identical arguments are skipped, and the runtime
    forces termination when the maximum number of iterations is reached.
    """

    def __init__(
        self,
        provider: LLMProvider,
        tool_executor: MonitoringToolExecutor | None = None,
        asset_loader: PromptAssetLoader | None = None,
        max_iterations: int = 10,
        verbose: bool = False,
    ) -> None:
        """Initialize the monitoring-agent runtime.

        Args:
            provider: LLM provider used to request the next action.
            tool_executor: Optional deterministic executor for app-level tools.
            asset_loader: Optional asset loader for prompts, tool docs, and
                skill fragments.
            max_iterations: Hard upper bound for the loop. This prevents the
                runtime from spinning forever if the LLM never returns a final
                report.
            verbose: When true, print a simplified live agent trace during
                standalone runs.
        """
        if max_iterations <= 0:
            raise ValueError("max_iterations must be > 0")
        resolved_loader: PromptAssetLoader = asset_loader or PromptAssetLoader()
        self.provider: LLMProvider = provider
        self.asset_loader: PromptAssetLoader = resolved_loader
        self.tool_executor: MonitoringToolExecutor = tool_executor or MonitoringToolExecutor(
            asset_loader=resolved_loader
        )
        self.max_iterations: int = max_iterations
        self.verbose: bool = verbose

    def run(
        self,
        *,
        job_name: MonitoringJobName,
        job_context: Mapping[str, JSONValue],
    ) -> MonitoringToolLoopResult:
        """Run the bounded monitoring-agent loop for one scheduled job.

        Flow:
        1. Build the fixed system prompt plus current job/tool context.
        2. Ask the LLM to either call one or more tools or return a final report.
        3. Execute requested tools deterministically.
        4. Append tool results to the next iteration context.
        5. Stop on final report, duplicate-only tool requests, empty response,
           or iteration limit.

        The runner does not decide whether a job should exist, whether a tool
        is globally allowed, or what environment is valid. Those decisions are
        made before the runner starts.
        """
        tool_results: list[MonitoringToolResult] = []
        trace: list[MonitoringAgentTraceEvent] = []
        seen_calls: set[str] = set()
        self._emit_trace(
            trace,
            MonitoringAgentTraceEvent(
                event_type=MonitoringAgentEventType.START,
                message=f"starting job={job_name.value}",
            ),
        )
        logger.info(
            "Starting monitoring agent loop: job=%s max_iterations=%d",
            job_name.value,
            self.max_iterations,
        )

        for iteration in range(1, self.max_iterations + 1):
            self._emit_trace(
                trace,
                MonitoringAgentTraceEvent(
                    event_type=MonitoringAgentEventType.ITERATION,
                    iteration=iteration,
                    message=f"iteration={iteration}",
                ),
            )
            logger.info(
                "Monitoring agent iteration started: job=%s iteration=%d tool_results=%d",
                job_name.value,
                iteration,
                len(tool_results),
            )
            self._emit_trace(
                trace,
                MonitoringAgentTraceEvent(
                    event_type=MonitoringAgentEventType.ASKING_LLM,
                    iteration=iteration,
                    message=f"iteration={iteration} asking_llm..",
                ),
            )
            system_prompt: str = self._build_system_prompt()
            user_message: str = self._build_user_message(
                job_name=job_name,
                job_context=job_context,
                tool_results=tool_results,
            )
            logger.debug(
                "Monitoring agent prompt sizes: system_chars=%d user_chars=%d",
                len(system_prompt),
                len(user_message),
            )
            response_text, _usage = self.provider.ask_question_with_usage(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.0,
            )
            if not response_text:
                logger.warning(
                    "Monitoring agent loop stopped: job=%s iteration=%d reason=empty_llm_response",
                    job_name.value,
                    iteration,
                )
                self._emit_trace(
                    trace,
                    MonitoringAgentTraceEvent(
                        event_type=MonitoringAgentEventType.STOP,
                        iteration=iteration,
                        message="stop_reason=empty_llm_response",
                    ),
                )
                return MonitoringToolLoopResult(
                    summary="Monitoring loop failed because the LLM returned no response.",
                    findings=["The LLM did not produce a tool decision or final report."],
                    tool_results=tool_results,
                    trace=trace,
                    final_payload={},
                    iterations=iteration,
                    stop_reason="empty_llm_response",
                )

            decision: MonitoringToolDecision = self._parse_decision(response_text)
            tool_names: list[str] = [tool_call.tool_name.value for tool_call in decision.tool_calls]
            decision_message: str
            if decision.action is MonitoringToolDecisionAction.CALL_TOOLS:
                decision_message = (
                    f"iteration={iteration} decision=call_tools tools=[{','.join(tool_names)}]"
                )
            else:
                decision_message = f"iteration={iteration} decision=final_report"
            self._emit_trace(
                trace,
                MonitoringAgentTraceEvent(
                    event_type=MonitoringAgentEventType.DECISION,
                    iteration=iteration,
                    message=decision_message,
                    decision_action=decision.action,
                ),
            )
            logger.info(
                "Monitoring agent decision received: job=%s iteration=%d action=%s tool_calls=%d",
                job_name.value,
                iteration,
                decision.action.value,
                len(decision.tool_calls),
            )
            if decision.action is MonitoringToolDecisionAction.FINAL_REPORT:
                logger.info(
                    "Monitoring agent loop finished: job=%s iteration=%d reason=final_report",
                    job_name.value,
                    iteration,
                )
                self._emit_trace(
                    trace,
                    MonitoringAgentTraceEvent(
                        event_type=MonitoringAgentEventType.STOP,
                        iteration=iteration,
                        message="stop_reason=final_report",
                    ),
                )
                logger.debug(
                    "Monitoring agent final summary preview: %s",
                    decision.summary[:200],
                )
                return MonitoringToolLoopResult(
                    summary=decision.summary,
                    findings=decision.findings,
                    tool_results=tool_results,
                    trace=trace,
                    final_payload=decision.payload,
                    iterations=iteration,
                    stop_reason="final_report",
                )

            executed_any: bool = False
            for tool_call in decision.tool_calls:
                call_signature: str = self._build_call_signature(tool_call)
                if call_signature in seen_calls:
                    self._emit_trace(
                        trace,
                        MonitoringAgentTraceEvent(
                            event_type=MonitoringAgentEventType.TOOL_SKIPPED,
                            iteration=iteration,
                            tool_name=tool_call.tool_name,
                            message=(
                                f"iteration={iteration} "
                                f"tool={tool_call.tool_name.value} "
                                "skipped_duplicate"
                            ),
                        ),
                    )
                    logger.info(
                        "Skipping duplicate monitoring tool call: job=%s iteration=%d tool=%s",
                        job_name.value,
                        iteration,
                        tool_call.tool_name.value,
                    )
                    continue
                seen_calls.add(call_signature)
                self._emit_trace(
                    trace,
                    MonitoringAgentTraceEvent(
                        event_type=MonitoringAgentEventType.TOOL_START,
                        iteration=iteration,
                        tool_name=tool_call.tool_name,
                        message=f"iteration={iteration} tool={tool_call.tool_name.value} start..",
                    ),
                )
                tool_result: MonitoringToolResult = self.tool_executor.execute(
                    tool_call,
                    job_name=job_name,
                    job_context=job_context,
                )
                tool_results.append(tool_result)
                executed_any = True
                self._emit_trace(
                    trace,
                    MonitoringAgentTraceEvent(
                        event_type=MonitoringAgentEventType.TOOL_DONE,
                        iteration=iteration,
                        tool_name=tool_result.tool_name,
                        message=(
                            f"iteration={iteration} " f"tool={tool_result.tool_name.value} " "done"
                        ),
                    ),
                )
                logger.info(
                    "Monitoring tool completed: job=%s iteration=%d tool=%s",
                    job_name.value,
                    iteration,
                    tool_result.tool_name.value,
                )
                logger.debug(
                    "Monitoring tool payload keys: tool=%s keys=%s",
                    tool_result.tool_name.value,
                    sorted(tool_result.payload.keys()),
                )

            if not executed_any:
                logger.warning(
                    "Monitoring agent loop stopped: job=%s iteration=%d reason=duplicate_tool_call",
                    job_name.value,
                    iteration,
                )
                self._emit_trace(
                    trace,
                    MonitoringAgentTraceEvent(
                        event_type=MonitoringAgentEventType.STOP,
                        iteration=iteration,
                        message="stop_reason=duplicate_tool_call",
                    ),
                )
                return MonitoringToolLoopResult(
                    summary="Monitoring loop stopped because only duplicate tool calls remained.",
                    findings=[
                        "The LLM requested tool calls that had already been "
                        "executed with the same arguments."
                    ],
                    tool_results=tool_results,
                    trace=trace,
                    final_payload={},
                    iterations=iteration,
                    stop_reason="duplicate_tool_call",
                )

        logger.warning(
            "Monitoring agent loop stopped: job=%s reason=max_iterations limit=%d",
            job_name.value,
            self.max_iterations,
        )
        self._emit_trace(
            trace,
            MonitoringAgentTraceEvent(
                event_type=MonitoringAgentEventType.STOP,
                iteration=self.max_iterations,
                message="stop_reason=max_iterations",
            ),
        )
        return MonitoringToolLoopResult(
            summary="Monitoring loop reached the maximum iteration limit before finalizing.",
            findings=[
                "The LLM did not return a final report within the allowed number of iterations."
            ],
            tool_results=tool_results,
            trace=trace,
            final_payload={},
            iterations=self.max_iterations,
            stop_reason="max_iterations",
        )

    def _emit_trace(
        self,
        trace: list[MonitoringAgentTraceEvent],
        event: MonitoringAgentTraceEvent,
    ) -> None:
        """Store a trace event and optionally print it for standalone debugging."""
        trace.append(event)
        if self.verbose:
            print(f"[monitoring-agent] {event.message}")

    def _build_system_prompt(self) -> str:
        """Compose the fixed system prompt for the bounded monitoring-agent loop."""
        sections: list[str] = [
            self.asset_loader.load_text("prompts/monitoring_tool_loop_system.md"),
            self.asset_loader.load_text("prompts/monitoring_tool_loop_user.md"),
            self.asset_loader.load_text("prompts/monitoring_job_rules.md"),
            "Use the response schema in monitoring_tool_loop_response.schema.json.",
        ]
        return "\n\n".join(section.strip() for section in sections if section.strip())

    def _build_user_message(
        self,
        *,
        job_name: MonitoringJobName,
        job_context: Mapping[str, JSONValue],
        tool_results: list[MonitoringToolResult],
    ) -> str:
        """Serialize the current job context, tools, and prior tool results for the LLM."""
        tool_definitions: JSONArray = []
        for definition in MonitoringToolRegistry.get_definitions():
            when_to_use: JSONArray = [item for item in definition.when_to_use]
            when_not_to_use: JSONArray = [item for item in definition.when_not_to_use]
            tool_definitions.append(
                {
                    "tool_name": definition.tool_name.value,
                    "description": definition.description,
                    "documentation": self.asset_loader.load_text(definition.documentation_asset),
                    "when_to_use": when_to_use,
                    "when_not_to_use": when_not_to_use,
                }
            )

        tool_result_payloads: JSONArray = [
            {
                "tool_name": result.tool_name.value,
                "payload": result.payload,
            }
            for result in tool_results
        ]
        payload: JSONObject = {
            "job_name": job_name.value,
            "job_context": dict(job_context),
            "available_tools": tool_definitions,
            "tool_results": tool_result_payloads,
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    def _parse_decision(self, response_text: str) -> MonitoringToolDecision:
        """Parse the LLM response into a structured monitoring tool decision."""
        payload: JSONObject = self._normalize_decision_payload(
            self._load_json_object(response_text)
        )
        action_raw: str = str(payload.get("action", "")).strip()
        if not action_raw:
            logger.error(
                "Invalid monitoring agent response: missing action. Preview=%s",
                response_text[:500],
            )
            raise ValueError("Invalid monitoring agent response: missing top-level action")
        action: MonitoringToolDecisionAction = MonitoringToolDecisionAction(action_raw)

        if action is MonitoringToolDecisionAction.FINAL_REPORT:
            findings: list[str] = self._coerce_string_list(payload.get("findings", []))
            return MonitoringToolDecision(
                action=action,
                summary=str(payload.get("summary", "")),
                findings=findings,
                payload=payload,
            )

        tool_calls_raw: JSONValue = payload.get("tool_calls", [])
        if not isinstance(tool_calls_raw, list):
            raise ValueError("tool_calls must be a list")
        tool_calls: list[MonitoringToolCall] = []
        for item in tool_calls_raw:
            if not isinstance(item, dict):
                raise ValueError("tool_calls items must be objects")
            tool_name = MonitoringToolName(str(item.get("tool_name", "")).strip())
            arguments_raw: JSONValue = item.get("arguments", {})
            if not isinstance(arguments_raw, dict):
                raise ValueError("tool call arguments must be a dict")
            arguments: dict[str, str] = {
                str(key): str(value) for key, value in arguments_raw.items()
            }
            tool_calls.append(MonitoringToolCall(tool_name=tool_name, arguments=arguments))

        return MonitoringToolDecision(
            action=action,
            tool_calls=tool_calls,
        )

    @staticmethod
    def _normalize_decision_payload(payload: JSONObject) -> JSONObject:
        """Normalize common wrapper-style LLM responses into the expected top-level shape."""
        if "action" in payload:
            return payload

        final_report: JSONValue = payload.get("final_report")
        if isinstance(final_report, dict):
            normalized_final_report: JSONObject = dict(final_report)
            normalized_final_report["action"] = MonitoringToolDecisionAction.FINAL_REPORT.value
            if "findings" not in normalized_final_report:
                findings_raw: JSONValue = normalized_final_report.get("key_findings", [])
                if isinstance(findings_raw, list):
                    normalized_final_report["findings"] = [str(item) for item in findings_raw]
                elif isinstance(findings_raw, str):
                    normalized_final_report["findings"] = [findings_raw]
                else:
                    normalized_final_report["findings"] = []
            return normalized_final_report

        call_tools: JSONValue = payload.get("call_tools")
        if isinstance(call_tools, list):
            return {
                "action": MonitoringToolDecisionAction.CALL_TOOLS.value,
                "tool_calls": call_tools,
            }
        if isinstance(call_tools, dict):
            normalized_call_tools: JSONObject = dict(call_tools)
            normalized_call_tools["action"] = MonitoringToolDecisionAction.CALL_TOOLS.value
            return normalized_call_tools

        return payload

    @staticmethod
    def _build_call_signature(tool_call: MonitoringToolCall) -> str:
        """Build a stable signature used to detect duplicate tool calls."""
        return json.dumps(
            {
                "tool_name": tool_call.tool_name.value,
                "arguments": tool_call.arguments,
            },
            sort_keys=True,
        )

    @staticmethod
    def _coerce_string_list(value: JSONValue) -> list[str]:
        """Normalize an arbitrary value into a list of strings when possible."""
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    @staticmethod
    def _parse_json_object(raw_text: str, error_message: str) -> JSONObject:
        try:
            payload: JSONValue = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(error_message) from exc

        if not isinstance(payload, dict):
            raise ValueError(error_message)
        return payload

    @staticmethod
    def _load_json_object(response_text: str) -> JSONObject:
        """Load a JSON object from plain text, fenced JSON, or embedded JSON text."""
        error_message = "response must be a JSON object"
        try:
            return MonitoringToolLoopRunner._parse_json_object(response_text, error_message)
        except json.JSONDecodeError as exc:
            match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if match:
                return MonitoringToolLoopRunner._parse_json_object(match.group(1), error_message)
            start_index: int = response_text.find("{")
            end_index: int = response_text.rfind("}")
            if start_index != -1 and end_index != -1:
                return MonitoringToolLoopRunner._parse_json_object(
                    response_text[start_index : end_index + 1],
                    error_message,
                )
            raise ValueError(error_message) from exc
