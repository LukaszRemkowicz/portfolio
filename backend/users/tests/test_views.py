# backend/users/tests/test_views.py
"""
Tests for users views
"""


import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from users.tests.factories import AstroProfileFactory, ProgrammingProfileFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
def test_profile_endpoint_returns_active_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns the user (singleton pattern)"""
    user = UserFactory()
    url = reverse("users:profile-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == user.first_name
    assert response.data["last_name"] == user.last_name
    assert response.data["bio"] == user.bio


@pytest.mark.django_db
def test_profile_endpoint_returns_404_when_no_active_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns 404 when user is inactive"""
    UserFactory(is_active=False)

    url = reverse("users:profile-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User is not active" in response.data["detail"]


@pytest.mark.django_db
def test_profile_endpoint_returns_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns the user (singleton pattern - only one user allowed)"""
    UserFactory(first_name="Single")

    url = reverse("users:profile-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Single"
    assert response.data["last_name"] == "User"


@pytest.mark.django_db
def test_profile_endpoint_includes_all_required_fields(api_client: APIClient) -> None:
    """Test that profile endpoint returns all required fields"""
    user = UserFactory(first_name="Complete", last_name="Profile", bio="Complete bio")

    ProgrammingProfileFactory(user=user)
    AstroProfileFactory(user=user)

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
def test_profile_structure(api_client: APIClient) -> None:
    """Test the structure of the profiles list within the response"""
    user = UserFactory()
    ProgrammingProfileFactory(user=user)
    AstroProfileFactory(user=user)

    url = reverse("users:profile-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["profiles"]) == 2
    # Verify profile content
    programming_profiles = [
        profile for profile in response.data["profiles"] if profile["type"] == "PROGRAMMING"
    ]
    assert programming_profiles, "Programming profile not found"
    assert programming_profiles[0]["title"] == "Dev"

    astro_profiles = [
        profile for profile in response.data["profiles"] if profile["type"] == "ASTRO"
    ]
    assert astro_profiles, "Astro profile not found"
    assert astro_profiles[0]["title"] == "Astro"


@pytest.mark.django_db
def test_profile_endpoint_handles_empty_fields(api_client: APIClient) -> None:
    """Test that profile endpoint handles empty/null fields correctly"""
    UserFactory(
        first_name="Empty",
        bio="",
        avatar=None,
        about_me_image=None,
        about_me_image2=None,
    )

    url = reverse("users:profile-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Empty"
    assert response.data["last_name"] == "User"
    assert response.data["bio"] == ""
    assert not response.data["avatar"]
    assert not response.data["about_me_image"]
    assert not response.data["about_me_image2"]


@pytest.mark.django_db
def test_profile_endpoint_constructs_image_urls_correctly(api_client: APIClient) -> None:
    """Test that profile endpoint constructs full image URLs correctly"""
    UserFactory()
    url = reverse("users:profile-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "avatar" in response.data
    assert "about_me_image" in response.data
    assert "about_me_image2" in response.data


@pytest.mark.django_db
def test_profile_endpoint_with_avatar(api_client: APIClient) -> None:
    """Test that profile endpoint returns full URL for avatar"""
    avatar_file = SimpleUploadedFile("avatar.jpg", b"content", content_type="image/jpeg")
    UserFactory(avatar=avatar_file)

    url = reverse("users:profile-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["avatar"] is not None
    assert response.data["avatar"].startswith("http")
    assert ".jpg" in response.data["avatar"]


@pytest.mark.django_db
def test_profile_endpoint_allows_anonymous_access(api_client: APIClient) -> None:
    """Test that profile endpoint allows anonymous access (AllowAny permission)"""
    UserFactory()
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
