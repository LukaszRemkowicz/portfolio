Return JSON only — no explanatory text outside the JSON:
{
  "summary": "Brief overview of the day's log health (2-3 sentences)",
  "severity": "INFO|WARNING|CRITICAL",
  "key_findings": ["specific finding 1", "specific finding 2"],
  "recommendations": "Concrete next steps referencing this project's code and services",
  "trend_summary": "1-2 sentences on what changed vs. prior days (e.g. attack calmed down)"
}
