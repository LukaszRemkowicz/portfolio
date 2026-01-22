# backend/core/utils/logging.py
from typing import Any


def sanitize_for_logging(value: Any) -> str:
    """
    Sanitize a value for logging to prevent log injection (CRLF removal).
    Also truncates extremely long strings.
    """
    if value is None:
        return ""

    # Remove control characters that could be used for log injection
    sanitized = str(value).replace("\n", " ").replace("\r", " ")

    # Truncate if too long (standard log safety)
    if len(sanitized) > 500:
        sanitized = sanitized[:497] + "..."

    return sanitized
