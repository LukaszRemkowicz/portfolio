# backend/users/serializers.py
from rest_framework import serializers

from .models import Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for niche-specific profile content"""

    class Meta:
        model = Profile
        fields = [
            "type",
            "is_active",
            "title",
            "specific_bio",
            "github_url",
            "linkedin_url",
            "astrobin_url",
            "fb_url",
            "ig_url",
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model profile with nested profiles"""

    profiles = ProfileSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "short_description",
            "bio",
            "avatar",
            "about_me_image",
            "about_me_image2",
            "profiles",
        ]
