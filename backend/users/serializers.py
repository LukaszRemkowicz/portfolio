# backend/users/serializers.py
from rest_framework import serializers

from translation.services import TranslationService

from .models import Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for niche-specific profile content"""

    def to_representation(self, instance: Profile) -> dict:
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang and lang != "en":
            for field in ["title", "specific_bio"]:
                if field in data:
                    data[field] = TranslationService.get_translation(instance, field, lang)
        return data

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

    def to_representation(self, instance: User) -> dict:
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang and lang != "en":
            for field in ["short_description", "bio"]:
                if field in data:
                    data[field] = TranslationService.get_translation(instance, field, lang)
        return data

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "short_description",
            "bio",
            "contact_email",
            "avatar",
            "about_me_image",
            "about_me_image2",
            "profiles",
        ]
