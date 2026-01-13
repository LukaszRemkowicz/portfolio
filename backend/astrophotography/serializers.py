from rest_framework import serializers

from .models import AstroImage, BackgroundMainPage


class AstroImageSerializerList(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")

    class Meta:
        model = AstroImage
        fields = ["pk", "url"]


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
