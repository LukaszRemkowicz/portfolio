## KNOWN NORMAL LOG PATTERNS — do NOT flag as issues

- `GET /health` or `/ping/` — Nginx health probes
- `[axes]` lockout entries after 5 failed admin logins — expected security behavior
- celery-worker task messages — normal operation
- celery-beat messages — normal only when the manual Beat profile is explicitly enabled
- `Replacing N existing analysis record(s)` — idempotent log analysis, not an error
- HTTP 304 Not Modified on static files — correct caching
- Parler translation fallback warnings — expected if Polish translation is missing
