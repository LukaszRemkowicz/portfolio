# backend/users/serializers.py
from rest_framework import serializers

from common.serializers import TranslatedSerializerMixin

from .models import Profile, User


class ProfileSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for niche-specific profile content"""

    def to_representation(self, instance: Profile) -> dict:
        data = super().to_representation(instance)
        return self.translate_fields(data=data, instance=instance, fields=["title", "specific_bio"])

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


class UserSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """Serializer for the User model profile with nested profiles"""

    profiles = ProfileSerializer(many=True, read_only=True)
    avatar = serializers.SerializerMethodField()
    about_me_image = serializers.SerializerMethodField()
    about_me_image2 = serializers.SerializerMethodField()

    def _build_media_version(self, obj: User) -> str:
        """Return a stable cache-busting token for user media URLs."""
        if not obj.updated_at:
            return ""
        return str(int(obj.updated_at.timestamp()))

    def _build_url(self, obj: User, source_field_name: str, webp_field_name: str) -> str:
        relative_url: str = obj._get_serving_image_url(source_field_name, webp_field_name)
        request = self.context.get("request")
        if relative_url and request:
            absolute_url = str(request.build_absolute_uri(relative_url))
            separator = "&" if "?" in absolute_url else "?"
            return f"{absolute_url}{separator}v={self._build_media_version(obj)}"
        return relative_url

    def get_avatar(self, obj: User) -> str:
        return self._build_url(obj, "avatar", "avatar_webp")

    def get_about_me_image(self, obj: User) -> str:
        return self._build_url(obj, "about_me_image", "about_me_image_webp")

    def get_about_me_image2(self, obj: User) -> str:
        return self._build_url(obj, "about_me_image2", "about_me_image2_webp")

    def to_representation(self, instance: User) -> dict:
        data = super().to_representation(instance)
        return self.translate_fields(
            data=data, instance=instance, fields=["short_description", "bio"]
        )

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
