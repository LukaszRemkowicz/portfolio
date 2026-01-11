# backend/users/tests/test_views.py
"""
Tests for users views
"""

from typing import Any
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from users.models import Profile

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.django_db
def test_profile_endpoint_returns_active_user(api_client: APIClient, user: User) -> None:
    """Test that profile endpoint returns the user (singleton pattern)"""
    # Simply update the user fixture with the specific bio we want to test

    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "first_name" in response.data
    assert "last_name" in response.data
    assert response.data["first_name"] == user.first_name
    assert response.data["last_name"] == user.last_name
    assert response.data["bio"] == user.bio


@pytest.mark.django_db
def test_profile_endpoint_returns_404_when_no_active_user(
    api_client: APIClient, user: User
) -> None:
    """Test that profile endpoint returns 404 when user is inactive"""
    # Simply set the user to inactive to test this case
    user.is_active = False
    user.save()

    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.data
    assert "User is not active" in response.data["detail"]


@pytest.mark.django_db
def test_profile_endpoint_returns_user(api_client: APIClient, user: User) -> None:
    """Test that profile endpoint returns the user (singleton pattern - only one user allowed)"""
    # Ensure user has specific name for assertion
    user.first_name = "Single"
    user.save()

    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Single"
    assert response.data["last_name"] == "User"


@pytest.mark.django_db
def test_profile_endpoint_includes_all_required_fields(api_client: APIClient, user: User) -> None:
    """Test that profile endpoint returns all required fields"""
    # Ensure user has complete data
    user.first_name = "Complete"
    user.last_name = "Profile"
    user.bio = "Complete bio"
    user.save()

    # Create persona profiles only once needed
    if not Profile.objects.filter(user=user).exists():
        Profile.objects.create(
            user=user,
            type=Profile.ProfileType.PROGRAMMING,
            title="Software Engineer",
            specific_bio="Code bio",
            github_url="https://github.com/user",
            linkedin_url="https://linkedin.com/in/user",
        )
        Profile.objects.create(
            user=user,
            type=Profile.ProfileType.ASTRO,
            title="Astrophotographer",
            specific_bio="Astro bio",
            astrobin_url="https://astrobin.com/users/user",
            fb_url="https://facebook.com/user",
            ig_url="https://instagram.com/user",
        )

    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    required_fields = [
        "first_name",
        "last_name",
        "bio",
        "avatar",
        "about_me_image",
        "about_me_image2",
        "profiles",
    ]
    for field in required_fields:
        assert field in response.data, f"Field {field} is missing from response"


@pytest.mark.django_db
def test_profile_structure(api_client: APIClient, user: User) -> None:
    """Test the structure of the profiles list within the response"""
    Profile.objects.create(
        user=user, type=Profile.ProfileType.PROGRAMMING, title="Dev", specific_bio="Bio"
    )
    Profile.objects.create(
        user=user, type=Profile.ProfileType.ASTRO, title="Astro", specific_bio="Bio"
    )

    url: str = reverse("users:profile-profile")
    response: Any = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["profiles"]) == 2
    # Verify profile content
    programming_profiles = [
        profile for profile in response.data["profiles"] if profile["type"] == "PROGRAMMING"
    ]
    assert programming_profiles, "Programming profile not found"
    programming_profile = programming_profiles[0]
    assert programming_profile["title"] == "Dev"
    assert programming_profile["github_url"] == ""

    astro_profiles = [
        profile for profile in response.data["profiles"] if profile["type"] == "ASTRO"
    ]
    assert astro_profiles, "Astro profile not found"
    astro_profile = astro_profiles[0]
    assert astro_profile["title"] == "Astro"
    assert astro_profile["astrobin_url"] == ""


@pytest.mark.django_db
def test_profile_endpoint_handles_empty_fields(api_client: APIClient, user: User) -> None:
    """Test that profile endpoint handles empty/null fields correctly"""
    user.first_name = "Empty"
    user.bio = ""  # Explicitly empty
    user.avatar = None
    user.about_me_image = None
    user.about_me_image2 = None
    user.save()

    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Empty"
    assert response.data["last_name"] == "User"
    assert response.data["bio"] == ""
    assert response.data["avatar"] is None or response.data["avatar"] == ""
    assert response.data["about_me_image"] is None or response.data["about_me_image"] == ""
    assert response.data["about_me_image2"] is None or response.data["about_me_image2"] == ""


@pytest.mark.django_db
def test_profile_endpoint_constructs_image_urls_correctly(
    api_client: APIClient, user: User
) -> None:
    """Test that profile endpoint constructs full image URLs correctly"""
    # Note: We can't easily set image paths in tests without actual files
    # But we can verify the URL construction logic works when paths exist
    # The actual image URL construction is tested by checking the response structure
    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    # Avatar, about_me_image, about_me_image2 should be in response
    assert "avatar" in response.data
    assert "about_me_image" in response.data
    assert "about_me_image2" in response.data
    # If image paths exist, they should be full URLs starting with media URL
    # (Branch with avatar is tested in test_profile_endpoint_with_avatar)


@pytest.mark.django_db
def test_profile_endpoint_with_avatar(api_client: APIClient, user: User) -> None:
    """Test that profile endpoint returns full URL for avatar"""
    # Create user with an avatar
    avatar = SimpleUploadedFile("avatar.jpg", b"content", content_type="image/jpeg")
    user.avatar = avatar
    user.save()

    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["avatar"] is not None
    # DRF ModelSerializer with 'request' in context returns absolute URLs
    assert response.data["avatar"].startswith("http")
    assert "avatar" in response.data["avatar"]
    assert ".jpg" in response.data["avatar"]


@pytest.mark.django_db
def test_profile_endpoint_handles_database_error(api_client: APIClient) -> None:
    """Test that profile endpoint handles database errors gracefully"""
    url: str = reverse("users:profile-profile")

    # Mock User.get_user to raise an exception
    with patch("users.views.User.get_user") as mock_get_user:
        mock_get_user.side_effect = Exception("Database connection error")

        response: Any = api_client.get(url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.data
        assert "Error retrieving profile" in response.data["detail"]


@pytest.mark.django_db
def test_profile_endpoint_allows_anonymous_access(api_client: APIClient, user: User) -> None:
    """Test that profile endpoint allows anonymous access (AllowAny permission)"""
    # Don't authenticate - should work without auth
    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "first_name" in response.data


@pytest.mark.django_db
def test_profile_endpoint_returns_404_when_no_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns 404 when no user exists"""
    # Ensure no users exist
    User.objects.all().delete()

    url = reverse("users:profile-profile")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.data
    assert "No user found" in response.data["detail"]
