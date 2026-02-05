# backend/core/throttling.py
"""
Custom throttling classes for the portfolio backend
"""

import logging
from typing import Any, Optional

from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, BaseThrottle

from django.core.cache import cache

logger = logging.getLogger(__name__)


class APIRateThrottle(AnonRateThrottle):
    """Custom throttle for general API calls"""

    scope = "api"


class GalleryRateThrottle(AnonRateThrottle):
    """
    Relaxed throttle for gallery views (images, background).
    Allows higher volume of requests for browsing.
    """

    scope = "gallery"


class ContactFormThrottle(BaseThrottle):
    """
    Enhanced throttle for contact form with IP + email combination tracking.
    More restrictive than standard throttling to prevent bot spam.
    Applied by DRF BEFORE validation (better for bot filtering).
    """

    def get_email_from_request(self, request: Request) -> Optional[str]:
        """Extract email from request data"""
        if hasattr(request, "data") and request.data:
            email: str = str(request.data.get("email", "")).lower().strip()
            return email if email else None
        return None

    def allow_request(self, request: Request, view: Any) -> bool:
        """Check if request should be allowed using multiple cache-based limits"""
        ip: str = self.get_ident(request)
        email: Optional[str] = self.get_email_from_request(request)

        # Define specific limits for keys
        limits = {
            f"contact_throttle_ip:{ip}": 5,  # 5 requests per hour per IP
        }

        if email:
            limits.update(
                {
                    f"contact_throttle_email:{email}": 3,  # 3 requests per hour per email
                    f"contact_throttle_combined:{ip}:{email}": 2,  # 2 req/hr per IP+email
                }
            )

        # 1. Check all triggers BEFORE incrementing any
        for key, limit in limits.items():
            count: int = cache.get(key, 0)
            if count >= limit:
                logger.warning(f"Contact form rate limit exceeded for key: {key}")
                return False

        # 2. If all checks pass, increment all counters safely
        for key in limits:
            try:
                cache.incr(key)
            except ValueError:
                # Key doesn't exist in cache, initialize it
                cache.set(key, 1, 3600)

        return True

    def wait(self) -> int:
        """Return wait time in seconds before retry is allowed"""
        return 3600
