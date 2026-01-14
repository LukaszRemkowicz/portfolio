from rest_framework import serializers

from .models import AstroImage, BackgroundMainPage


class AstroImageSerializerList(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = AstroImage
        fields = [
            "pk",
            "name",
            "description",
            "url",
            "thumbnail_url",
            "tags",
            "capture_date",
            "location",
            "celestial_object",
        ]


class AstroImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstroImage
        fields = [
            "capture_date",
            "equipment",
            "exposure_details",
            "celestial_object",
            "astrobin_url",
            "description",
        ]


class BackgroundMainPageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")

    class Meta:
        model = BackgroundMainPage
        fields = ["url"]
