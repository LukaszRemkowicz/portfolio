"""
Custom throttling classes for the portfolio backend
"""

from rest_framework.throttling import AnonRateThrottle


class ContactThrottle(AnonRateThrottle):
    """Custom throttle for contact form submissions - more restrictive for anonymous users"""

    scope = "contact"


class APIRateThrottle(AnonRateThrottle):
    """Custom throttle for general API calls"""

    scope = "api"
