import hashlib
import hmac
import time

from django.conf import settings
from django.utils.encoding import force_bytes


def generate_signature(resource_id: str, timestamp: int) -> str:
    """
    Generates an HMAC-SHA256 signature for a resource_id and timestamp.
    """
    secret = force_bytes(settings.SECRET_KEY)
    message = force_bytes(f"{resource_id}:{timestamp}")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def generate_signed_url_params(resource_id: str, expiration_seconds: int = 3600) -> dict:
    """
    Returns the query parameters (s, e) needed for a signed URL.
    """
    timestamp = int(time.time()) + expiration_seconds
    signature = generate_signature(resource_id, timestamp)
    return {"s": signature, "e": timestamp}


def validate_signed_url(resource_id: str, signature: str, timestamp_str: str) -> bool:
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
    expected_signature = generate_signature(resource_id, timestamp)
    return hmac.compare_digest(signature, expected_signature)
