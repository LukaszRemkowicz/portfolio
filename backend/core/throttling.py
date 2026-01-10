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


class ContactThrottle(AnonRateThrottle):
    """Custom throttle for contact form submissions - more restrictive for anonymous users"""

    scope = "contact"


class APIRateThrottle(AnonRateThrottle):
    """Custom throttle for general API calls"""

    scope = "api"


class ContactFormThrottle(BaseThrottle):
    """
    Enhanced throttle for contact form with IP + email combination tracking.
    More restrictive than standard throttling to prevent bot spam.
    Applied by DRF BEFORE validation (better for bot filtering).
    Frontend validation prevents valid users from being throttled on invalid submissions.
    """

    def get_ident(self, request: Request) -> str:
        """Get IP address from request"""
        x_forwarded_for: Optional[str] = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip: str = x_forwarded_for.split(",")[0].strip()
        else:
            ip = str(request.META.get("REMOTE_ADDR", "unknown"))
        return ip

    def get_email_from_request(self, request: Request) -> Optional[str]:
        """Extract email from request data"""
        if hasattr(request, "data") and request.data:
            email: str = request.data.get("email", "").lower().strip()
            return email if email else None
        return None

    def allow_request(self, request: Request, view: Any) -> bool:
        """Check if request should be allowed - IP-based throttling always applies"""
        ip: str = self.get_ident(request)
        email: Optional[str] = self.get_email_from_request(request)
        # Always throttle by IP (works even without email)
        cache_key_ip: str = f"contact_throttle_ip:{ip}"
        ip_count: int = cache.get(cache_key_ip, 0)
        # IP limit: 5/hour (applies to all requests)
        if ip_count >= 5:
            logger.warning(f"Contact form rate limit exceeded (IP): IP={ip}, IP_count={ip_count}")
            return False
        # If email is available, also check email-based limits
        if email:
            cache_key_email: str = f"contact_throttle_email:{email}"
            cache_key_combined: str = f"contact_throttle_combined:{ip}:{email}"
            email_count: int = cache.get(cache_key_email, 0)
            combined_count: int = cache.get(cache_key_combined, 0)
            # Email limits: 3/hour per email, 2/hour per IP+email combo
            if email_count >= 3 or combined_count >= 2:
                logger.warning(
                    f"Contact form rate limit exceeded: IP={ip}, Email={email}, "
                    f"IP_count={ip_count}, Email_count={email_count}, Combined_count={combined_count}"
                )
                return False
            # Increment email-based counters
            cache.set(cache_key_email, email_count + 1, 3600)
            cache.set(cache_key_combined, combined_count + 1, 3600)
        # Increment IP counter (always done)
        cache.set(cache_key_ip, ip_count + 1, 3600)
        return True

    def wait(self) -> int:
        """Return wait time in seconds before retry is allowed"""
        return 3600  # 1 hour
