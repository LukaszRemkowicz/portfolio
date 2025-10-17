from rest_framework import serializers
from .models import BackgroundMainPage

class BackgroundMainPageSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(source='image')

    class Meta:
        model = BackgroundMainPage
        fields = ['url'] 