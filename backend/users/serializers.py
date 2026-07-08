from typing import Any

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


class UserSerializer(
    TranslatedSerializerMixin,
    serializers.ModelSerializer,
):
    """Serializer for the User model profile with nested profiles"""

    profiles = ProfileSerializer(many=True, read_only=True)
    avatar = serializers.SerializerMethodField()
    about_me_image = serializers.SerializerMethodField()
    about_me_image2 = serializers.SerializerMethodField()

    def get_image_variants(self, obj: User, source_name: str) -> dict[str, Any]:
        role = "original_format"
        stored_role = obj._build_variant_role(role, source_name)
        fallback_image = obj.get_variant_candidates(stored_role, preferred_width=2560)

        return {
            "fallback_image": fallback_image[0] if fallback_image else None,
            "variants": {role: obj.get_variant_candidates(stored_role)},
        }

    def get_avatar(self, obj: User) -> dict[str, Any]:
        return self.get_image_variants(obj, source_name="avatar")

    def get_about_me_image(self, obj: User) -> dict[str, Any]:
        return self.get_image_variants(obj, source_name="about_me_image")

    def get_about_me_image2(self, obj: User) -> dict[str, Any]:
        return self.get_image_variants(obj, source_name="about_me_image2")

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
