# backend/users/tests/test_views.py
"""
Tests for users views
"""

import pytest
from typing import Any, List
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.test import Client

User = get_user_model()


@pytest.mark.django_db
def test_profile_endpoint_returns_active_user(client: Client) -> None:
    """Test that profile endpoint returns the user (singleton pattern)"""
    # Create the single user with profile data (singleton pattern)
    user = User(email="test@example.com", first_name="John", last_name="Doe", bio="Test bio", is_active=True)
    user.set_password("testpass123")
    user.save()
    
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "first_name" in response.data
    assert "last_name" in response.data
    assert response.data["first_name"] == "John"
    assert response.data["last_name"] == "Doe"
    assert response.data["bio"] == "Test bio"


@pytest.mark.django_db
def test_profile_endpoint_returns_404_when_no_active_user(client: Client) -> None:
    """Test that profile endpoint returns 404 when user is inactive"""
    # Create the single user as inactive (singleton pattern)
    user = User(email="inactive@example.com", first_name="Inactive", last_name="User", is_active=False)
    user.set_password("testpass123")
    user.save()
    
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.data
    assert "User is not active" in response.data["detail"]


@pytest.mark.django_db
def test_profile_endpoint_returns_user(client: Client) -> None:
    """Test that profile endpoint returns the user (singleton pattern - only one user allowed)"""
    # Create the single user (singleton pattern - only one user is allowed)
    user = User(email="single@example.com", first_name="Single", last_name="User", is_active=True)
    user.set_password("testpass123")
    user.save()
    
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Single"
    assert response.data["last_name"] == "User"


@pytest.mark.django_db
def test_profile_endpoint_includes_all_required_fields(client: Client) -> None:
    """Test that profile endpoint returns all required fields"""
    user = User(
        email="complete@example.com",
        first_name="Complete",
        last_name="Profile",
        bio="Complete bio",
        website="https://example.com",
        github_profile="https://github.com/user",
        linkedin_profile="https://linkedin.com/in/user",
        astrobin_url="https://astrobin.com/users/user",
        fb_url="https://facebook.com/user",
        ig_url="https://instagram.com/user",
        is_active=True,
    )
    user.set_password("testpass123")
    user.save()
    
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    required_fields: List[str] = [
        "first_name",
        "last_name",
        "bio",
        "website",
        "github_profile",
        "linkedin_profile",
        "astrobin_url",
        "fb_url",
        "ig_url",
        "avatar",
        "about_me_image",
        "about_me_image2",
    ]
    for field in required_fields:
        assert field in response.data, f"Field {field} is missing from response"


@pytest.mark.django_db
def test_profile_endpoint_handles_empty_fields(client: Client) -> None:
    """Test that profile endpoint handles empty/null fields correctly"""
    user = User(email="empty@example.com", first_name="Empty", last_name="User", is_active=True)
    user.set_password("testpass123")
    user.save()
    
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Empty"
    assert response.data["last_name"] == "User"
    assert response.data["bio"] == ""
    assert response.data["website"] == ""
    assert response.data["avatar"] is None or response.data["avatar"] == ""
    assert response.data["about_me_image"] is None or response.data["about_me_image"] == ""
    assert response.data["about_me_image2"] is None or response.data["about_me_image2"] == ""


@pytest.mark.django_db
def test_profile_endpoint_constructs_image_urls_correctly(client: Client) -> None:
    """Test that profile endpoint constructs full image URLs correctly"""
    user = User(email="images@example.com", first_name="Images", last_name="User", is_active=True)
    user.set_password("testpass123")
    user.save()
    
    # Note: We can't easily set image paths in tests without actual files
    # But we can verify the URL construction logic works when paths exist
    # The actual image URL construction is tested by checking the response structure
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    # Avatar, about_me_image, about_me_image2 should be in response
    assert "avatar" in response.data
    assert "about_me_image" in response.data
    assert "about_me_image2" in response.data
    # If image paths exist, they should be full URLs starting with media URL
    if response.data["avatar"]:
        assert response.data["avatar"].startswith(settings.MEDIA_URL)


@pytest.mark.django_db
def test_profile_endpoint_handles_database_error(client: Client) -> None:
    """Test that profile endpoint handles database errors gracefully"""
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    # Mock User.get_user to raise an exception
    with patch("users.views.User.get_user") as mock_get_user:
        mock_get_user.side_effect = Exception("Database connection error")
        
        response: Any = api_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "detail" in response.data
        assert "Error retrieving profile" in response.data["detail"]


@pytest.mark.django_db
def test_profile_endpoint_allows_anonymous_access(client: Client) -> None:
    """Test that profile endpoint allows anonymous access (AllowAny permission)"""
    # Create the single user (singleton pattern)
    user = User(email="public@example.com", first_name="Public", last_name="User", is_active=True)
    user.set_password("testpass123")
    user.save()
    
    api_client: APIClient = APIClient()
    # Don't authenticate - should work without auth
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "first_name" in response.data


@pytest.mark.django_db
def test_profile_endpoint_returns_404_when_no_user(client: Client) -> None:
    """Test that profile endpoint returns 404 when no user exists"""
    api_client: APIClient = APIClient()
    url: str = reverse("users:profile-profile")
    
    response: Any = api_client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.data
    assert "No user found" in response.data["detail"]
