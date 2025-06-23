from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model"""
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'avatar',
            'website',
            'github_profile',
            'linkedin_profile',
            'astrobin_url',
            'fb_url',
            'ig_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'email': {'required': True}
        }

    def create(self, validated_data):
        """Create and return a new user with encrypted password"""
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return an existing user"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user

class PublicUserSerializer(serializers.ModelSerializer):
    """Serializer for public user profile viewing"""
    
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'bio',
            'avatar',
            'about_me_image',
            'about_me_image2',
            'website',
            'github_profile',
            'linkedin_profile',
            'astrobin_url',
            'fb_url',
            'ig_url'
        ]
        read_only_fields = fields  # All fields are read-only for public viewing 