from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from django.contrib.auth import get_user_model

from core.throttling import APIRateThrottle

User = get_user_model()


class UserViewSet(viewsets.ViewSet):
    """ViewSet for retrieving the user profile"""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [APIRateThrottle, UserRateThrottle]

    @action(detail=False, methods=["get"])
    def profile(self, request):
        """Get the user profile"""
        # Get the first active user (assuming this is a single-user portfolio)
        # Note: Database may have display_name instead of username
        # Using raw SQL to avoid username column issues
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, first_name, last_name, bio, avatar, about_me_image, 
                           about_me_image2, website, github_profile, linkedin_profile, 
                           astrobin_url, fb_url, ig_url
                    FROM users_user 
                    WHERE is_active = TRUE 
                    ORDER BY id ASC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                
                if not row:
                    return Response({"detail": "No active user found."}, status=status.HTTP_404_NOT_FOUND)
                
                user_id = row[0]
                data = {
                    "first_name": row[1] or "",
                    "last_name": row[2] or "",
                    "bio": row[3] or "",
                    "website": row[7] or "",
                    "github_profile": row[8] or "",
                    "linkedin_profile": row[9] or "",
                    "astrobin_url": row[10] or "",
                    "fb_url": row[11] or "",
                    "ig_url": row[12] or "",
                }
                
                # Get image URLs from database - construct URLs manually
                avatar_path = row[4]
                about_me_image_path = row[5]
                about_me_image2_path = row[6]
                
                # Construct full URLs for images if paths exist
                from django.conf import settings
                media_url = settings.MEDIA_URL
                data["avatar"] = f"{media_url}{avatar_path}" if avatar_path else None
                data["about_me_image"] = f"{media_url}{about_me_image_path}" if about_me_image_path else None
                data["about_me_image2"] = f"{media_url}{about_me_image2_path}" if about_me_image2_path else None
                
                return Response(data)
        except Exception as e:
            return Response(
                {"detail": f"Error retrieving profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
