from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .serializers import PublicUserSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action

User = get_user_model()

class UserViewSet(viewsets.ViewSet):
    """ViewSet for retrieving the user profile"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get the user profile"""
        # Get the first active user (assuming this is a single-user portfolio)
        user = get_object_or_404(User.objects.filter(is_active=True).only(
            'username', 'first_name', 'last_name', 'bio',
            'avatar', 'about_me_image', 'about_me_image2', 'website', 'github_profile', 'linkedin_profile',
            'astrobin_url', 'fb_url', 'ig_url'
        ))
        serializer = PublicUserSerializer(user)
        return Response(serializer.data)
