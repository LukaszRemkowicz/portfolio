def sanitize_for_log(value: str | None) -> str:
    """Sanitizes a string for logging by removing control characters."""
    if value is None:
        return "None"
    return str(value).replace("\n", "").replace("\r", "")
