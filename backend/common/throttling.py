import logging
from typing import Any

from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, BaseThrottle

from django.conf import settings
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

    def get_email_from_request(self, request: Request) -> str | None:
        """Extract email from request data"""
        if hasattr(request, "data") and request.data:
            email: str = str(request.data.get("email", "")).lower().strip()
            return email if email else None
        return None

    def allow_request(self, request: Request, view: Any) -> bool:
        """Check if request should be allowed using multiple cache-based limits"""
        if settings.DEBUG:
            return True

        try:
            ip: str = self.get_ident(request)
            email: str | None = self.get_email_from_request(request)

            limits = {
                f"contact_throttle_ip:{ip}": 5,
            }

            if email:
                limits.update(
                    {
                        f"contact_throttle_email:{email}": 3,
                        f"contact_throttle_combined:{ip}:{email}": 2,
                    }
                )

            for key, limit in limits.items():
                count: int = cache.get(key, 0)
                if count >= limit:
                    logger.warning(f"Contact form rate limit exceeded for key: {key}")
                    return False

            for key in limits:
                try:
                    cache.incr(key)
                except ValueError:
                    cache.set(key, 1, 3600)

            return True
        except Exception as exc:
            logger.warning("Contact form throttle unavailable, allowing request: %s", exc)
            return True

    def wait(self) -> int:
        """Return wait time in seconds before retry is allowed"""
        return 3600
