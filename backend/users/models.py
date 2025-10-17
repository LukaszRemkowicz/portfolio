from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with additional fields"""

    bio = models.TextField(max_length=10000, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    about_me_image = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    about_me_image2 = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)
    github_profile = models.URLField(max_length=200, blank=True)
    linkedin_profile = models.URLField(max_length=200, blank=True)
    astrobin_url = models.URLField(
        max_length=200,
        blank=True,
        help_text=(
            "Your Astrobin profile URL " "(e.g., https://www.astrobin.com/users/yourusername/)"
        ),
    )
    fb_url = models.URLField(
        max_length=200, blank=True, help_text="Your Facebook profile or page URL"
    )
    ig_url = models.URLField(
        max_length=200,
        blank=True,
        help_text=("Your Instagram profile URL " "(e.g., https://www.instagram.com/yourusername/)"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username
