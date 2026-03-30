# Monitoring Tool Loop User Prompt

You must respond with JSON only.

Choose one action:
- `call_tools`
- `final_report`

Use `call_tools` when you still need data or a project skill fragment.
Use `final_report` when you have enough information to finish the job.

You may request one or more tools in a single step.

Required top-level response shapes:

For tool calls:
```json
{
  "action": "call_tools",
  "tool_calls": [
    {
      "tool_name": "prepare_log_report",
      "arguments": {}
    }
  ]
}
```

For final report:
```json
{
  "action": "final_report",
  "summary": "Short overall summary",
  "findings": ["Finding 1", "Finding 2"],
  "severity": "INFO|WARNING|CRITICAL",
  "key_findings": ["Specific finding 1", "Specific finding 2"],
  "recommendations": "Concrete next steps",
  "trend_summary": "Short change summary"
}
```

Do not return:
```json
{
  "final_report": {
    "summary": "..."
  }
}
```
