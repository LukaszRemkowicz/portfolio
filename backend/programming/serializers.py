from rest_framework import serializers

from .models import Project, ProjectImage


class ProjectImageSerializer(serializers.ModelSerializer):
    """Serializer for project-specific images"""

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
