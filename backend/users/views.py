# backend/users/views.py
from typing import Any

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from django.contrib.auth import get_user_model
from django.conf import settings

from core.throttling import APIRateThrottle

User = get_user_model()


class UserViewSet(viewsets.ViewSet):
    """ViewSet for retrieving the user profile"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [APIRateThrottle, UserRateThrottle]

    @action(detail=False, methods=["get"])
    def profile(self, request: Request) -> Response:
        """Get the user profile (singleton pattern: only one user exists)"""
        try:
            user = User.get_user()

            if not user:
                return Response(
                    {"detail": "No user found."}, status=status.HTTP_404_NOT_FOUND
                )

            if not user.is_active:
                return Response(
                    {"detail": "User is not active."}, status=status.HTTP_404_NOT_FOUND
                )

            # Construct full URLs for images if paths exist
            media_url: str = settings.MEDIA_URL

            data: dict[str, Any] = {
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "bio": user.bio or "",
                "website": user.website or "",
                "github_profile": user.github_profile or "",
                "linkedin_profile": user.linkedin_profile or "",
                "astrobin_url": user.astrobin_url or "",
                "fb_url": user.fb_url or "",
                "ig_url": user.ig_url or "",
                "avatar": f"{media_url}{user.avatar}" if user.avatar else None,
                "about_me_image": f"{media_url}{user.about_me_image}" if user.about_me_image else None,
                "about_me_image2": f"{media_url}{user.about_me_image2}" if user.about_me_image2 else None,
            }

            return Response(data)
        except Exception as error:
            return Response(
                {"detail": f"Error retrieving profile: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
