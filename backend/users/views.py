# backend/users/views.py

import logging

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from django.contrib.auth import get_user_model

from core.throttling import APIRateThrottle

from .serializers import UserSerializer

User = get_user_model()


logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ViewSet):
    """ViewSet for retrieving the singleton user profile"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [APIRateThrottle, UserRateThrottle]
    http_method_names = ["get", "head", "options"]

    @action(detail=False, methods=["get"])
    def profile(self, request: Request) -> Response:
        """Get the user profile (singleton pattern: only one user exists)"""
        user = User.get_user()

        if not user:
            return Response({"detail": "No user found."}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({"detail": "User is not active."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, context={"request": request})
        return Response(serializer.data)
