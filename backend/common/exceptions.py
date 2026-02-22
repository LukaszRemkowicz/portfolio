# backend/common/exceptions.py


class LLMAuthenticationError(Exception):
    """Raised when the LLM provider rejects the API key or authentication."""

    pass
