def sanitize_for_logging(value: str | None) -> str:
    """
    Sanitize a string for logging to prevent log injection (CRLF removal).
    Also truncates extremely long strings.
    """
    if not value:
        return ""

    # Remove control characters that could be used for log injection
    # Replace with space to preserve word separation
    sanitized = value.replace("\n", " ").replace("\r", " ")

    # Truncate if too long (standard log safety)
    if len(sanitized) > 500:
        sanitized = sanitized[:497] + "..."

    return sanitized
