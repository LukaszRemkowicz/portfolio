from rest_framework import serializers
from .models import BackgroundMainPage, AstroImage

class AstroImageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source='path')

    class Meta:
        model = AstroImage
        fields = ['pk', 'url']

class BackgroundMainPageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source='image')

    class Meta:
        model = BackgroundMainPage
        fields = ['url'] 