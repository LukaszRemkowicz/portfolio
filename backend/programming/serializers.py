from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers

from django.conf import settings

from translation.services import TranslationService

from .models import Project, ProjectImage


class ProjectImageSerializer(TranslatableModelSerializer):
    """Serializer for project-specific images"""

    def to_representation(self, instance: ProjectImage) -> dict:
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang = request.query_params.get("lang") if request else None

        if lang and lang != settings.DEFAULT_APP_LANGUAGE:
            for field in ["name", "description"]:
                if field in data:
                    data[field] = TranslationService.get_translation(instance, field, lang)

        return data  # type: ignore[no-any-return]

    class Meta:
        model = ProjectImage
        fields = ["pk", "url", "thumbnail_url", "is_cover", "name"]


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for programming projects including nested images"""

    images = ProjectImageSerializer(many=True, read_only=True)
    technologies_list = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "pk",
            "name",
            "description",
            "technologies",
            "technologies_list",
            "github_url",
            "live_url",
            "images",
            "created_at",
            "updated_at",
        ]

    def get_technologies_list(self, obj):
        """Parse comma-separated technologies into a list"""
        if obj.technologies:
            return [tech.strip() for tech in obj.technologies.split(",")]
        return []
