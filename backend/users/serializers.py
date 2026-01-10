# backend/users/serializers.py
from rest_framework import serializers

from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model profile"""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "bio",
            "avatar",
            "about_me_image",
            "about_me_image2",
            "website",
            "github_profile",
            "linkedin_profile",
            "astrobin_url",
            "fb_url",
            "ig_url",
        ]
