import hashlib
import hmac
import time

from django.conf import settings
from django.utils.encoding import force_bytes


def generate_signature(slug: str, timestamp: int) -> str:
    """
    Generates an HMAC-SHA256 signature for a slug and timestamp.
    """
    secret = force_bytes(settings.SECRET_KEY)
    message = force_bytes(f"{slug}:{timestamp}")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def generate_signed_url_params(slug: str, expiration_seconds: int = 3600) -> dict:
    """
    Returns the query parameters (s, e) needed for a signed URL.
    """
    timestamp = int(time.time()) + expiration_seconds
    signature = generate_signature(slug, timestamp)
    return {"s": signature, "e": timestamp}


def validate_signed_url(slug: str, signature: str, timestamp_str: str) -> bool:
    """
    Validates the signature and checks for expiration.
    Returns True if valid, False otherwise.
    """
    try:
        timestamp = int(timestamp_str)
    except (ValueError, TypeError):
        return False

    # Check expiration
    if timestamp < int(time.time()):
        return False

    # Check signature
    expected_signature = generate_signature(slug, timestamp)
    return hmac.compare_digest(signature, expected_signature)
