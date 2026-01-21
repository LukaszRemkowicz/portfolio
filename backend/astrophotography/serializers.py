from rest_framework import serializers

from .models import AstroImage, MainPageBackgroundImage, MainPageLocation, Place


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["id", "name"]


class AstroImageSerializerList(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)
    tags = serializers.StringRelatedField(many=True)
    location = serializers.CharField()

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
            "created_at",
        ]


class AstroImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstroImage
        fields = [
            "capture_date",
            "telescope",
            "camera",
            "tracker",
            "tripod",
            "lens",
            "exposure_details",
            "celestial_object",
            "astrobin_url",
            "description",
        ]


class MainPageBackgroundImageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")

    class Meta:
        model = MainPageBackgroundImage
        fields = ["url"]


class AstroImageThumbnailSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source="path")
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)

    class Meta:
        model = AstroImage
        fields = ["pk", "url", "thumbnail_url", "description"]


class MainPageLocationSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source="place.name", read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True)
    images = AstroImageThumbnailSerializer(many=True, read_only=True)
    background_image = serializers.SerializerMethodField()

    def get_background_image(self, obj):
        if obj.background_image:
            return obj.background_image.path.url
        return None

    class Meta:
        model = MainPageLocation
        fields = [
            "pk",
            "country",
            "country_name",
            "country_slug",
            "place_name",
            "place_slug",
            "highlight_name",
            "story",
            "background_image",
            "images",
            "created_at",
        ]
