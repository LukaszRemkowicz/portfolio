# backend/users/tests/test_views.py
"""
Tests for users views
"""

from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from common.tests.image_helpers import jpeg_field
from core.models import ImageVariant
from core.tasks import process_image_task
from core.tests.factories import ImageVariantFactory
from users.models import User as PortfolioUser
from users.tests.factories import AstroProfileFactory, ProgrammingProfileFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
def test_profile_endpoint_returns_active_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns the user (singleton pattern)"""
    user: PortfolioUser = UserFactory()
    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == user.first_name
    assert response.data["last_name"] == user.last_name
    assert response.data["bio"] == user.bio


@pytest.mark.django_db
def test_profile_endpoint_returns_404_when_no_active_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns 404 when user is inactive"""
    UserFactory(is_active=False)

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User is not active" in response.data["detail"]


@pytest.mark.django_db
def test_profile_endpoint_returns_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns the user (singleton pattern - only one user allowed)"""
    UserFactory(first_name="Single")

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Single"
    assert response.data["last_name"] == "User"


@pytest.mark.django_db
def test_profile_endpoint_includes_all_required_fields(api_client: APIClient) -> None:
    """Test that profile endpoint returns all required fields"""
    user: PortfolioUser = UserFactory(
        first_name="Complete", last_name="Profile", bio="Complete bio"
    )

    ProgrammingProfileFactory(user=user)
    AstroProfileFactory(user=user)

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    required_fields: list[str] = [
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
    user: PortfolioUser = UserFactory()
    ProgrammingProfileFactory(user=user)
    AstroProfileFactory(user=user)

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)
    profiles: list[dict[str, str]] = response.data["profiles"]

    assert response.status_code == status.HTTP_200_OK
    assert len(profiles) == 2
    # Verify profile content
    programming_profiles: list[dict[str, str]] = [
        profile for profile in profiles if profile["type"] == "PROGRAMMING"
    ]
    assert programming_profiles, "Programming profile not found"
    assert programming_profiles[0]["title"] == "Dev"

    astro_profiles: list[dict[str, str]] = [
        profile for profile in profiles if profile["type"] == "ASTRO"
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

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Empty"
    assert response.data["last_name"] == "User"
    assert response.data["bio"] == ""
    assert response.data["avatar"] == {
        "fallback_image": None,
        "variants": {"original_format": []},
    }
    assert response.data["about_me_image"] == {
        "fallback_image": None,
        "variants": {"original_format": []},
    }
    assert response.data["about_me_image2"] == {
        "fallback_image": None,
        "variants": {"original_format": []},
    }


@pytest.mark.django_db
def test_profile_endpoint_constructs_image_urls_correctly(api_client: APIClient) -> None:
    """Test that profile endpoint constructs full image URLs correctly"""
    UserFactory()
    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "avatar" in response.data
    assert "about_me_image" in response.data
    assert "about_me_image2" in response.data


@pytest.mark.django_db
def test_profile_endpoint_with_avatar(api_client: APIClient) -> None:
    """Test that profile endpoint returns empty candidates before variant sync."""
    avatar_file: SimpleUploadedFile = jpeg_field("avatar.jpg", size=(800, 800))
    with patch("users.models.process_image_task.delay_on_commit"):
        UserFactory(avatar=avatar_file)

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["avatar"] == {
        "fallback_image": None,
        "variants": {"original_format": []},
    }


@pytest.mark.django_db
def test_profile_endpoint_allows_anonymous_access(api_client: APIClient) -> None:
    """Test that profile endpoint allows anonymous access (AllowAny permission)"""
    UserFactory()
    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "first_name" in response.data


@pytest.mark.django_db
def test_profile_endpoint_returns_404_when_no_user(api_client: APIClient) -> None:
    """Test that profile endpoint returns 404 when no user exists"""
    # Ensure no users exist
    User.objects.all().delete()

    url: str = reverse("users:profile-profile")

    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.data
    assert "No user found" in response.data["detail"]


# ---------------------------------------------------------------------------
# Generated-variant integration tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_profile_avatar_serves_generated_variant_url(api_client: APIClient) -> None:
    """Integration: profile endpoint returns the generated original_format candidate."""
    user: PortfolioUser = UserFactory(avatar=jpeg_field("photo_legacy.jpg", size=(800, 800)))
    process_image_task("users", "User", user.pk, ["avatar"])

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    avatar = response.data["avatar"]
    assert avatar["fallback_image"], "avatar fallback candidate should not be empty"
    assert ".webp" in avatar["fallback_image"]["url"]
    assert avatar["variants"]["original_format"] == [avatar["fallback_image"]]


@pytest.mark.django_db
def test_profile_image_fields_return_stored_variant_urls(api_client: APIClient) -> None:
    with patch("users.models.process_image_task.delay_on_commit"):
        user: PortfolioUser = UserFactory(
            avatar=jpeg_field("avatar.jpg", size=(800, 800)),
            about_me_image=jpeg_field("about-me.jpg", size=(1200, 800)),
            about_me_image2=jpeg_field("about-me-2.jpg", size=(1200, 800)),
        )
    avatar: ImageVariant = ImageVariantFactory(
        owner=user,
        file__filename="avatar-original-format.webp",
        role="avatar__original_format",
        width=800,
        height=800,
    )
    about_me: ImageVariant = ImageVariantFactory(
        owner=user,
        file__filename="about-me-original-format.webp",
        role="about_me_image__original_format",
        width=1200,
        height=800,
    )
    about_me2: ImageVariant = ImageVariantFactory(
        owner=user,
        file__filename="about-me-2-original-format.webp",
        role="about_me_image2__original_format",
        width=1200,
        height=800,
    )

    response: Response = api_client.get(reverse("users:profile-profile"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["avatar"]["fallback_image"]["url"] == avatar.file.url
    assert response.data["about_me_image"]["fallback_image"]["url"] == about_me.file.url
    assert response.data["about_me_image2"]["fallback_image"]["url"] == about_me2.file.url


@pytest.mark.django_db
def test_profile_image_fields_ignore_requested_size(api_client: APIClient) -> None:
    with patch("users.models.process_image_task.delay_on_commit"):
        user: PortfolioUser = UserFactory(avatar=jpeg_field("avatar.jpg", size=(1200, 1200)))
    requested_avatar: ImageVariant = ImageVariantFactory(
        owner=user,
        file__filename="avatar-640.webp",
        role="avatar__original_format",
        width=640,
        height=640,
    )
    default_avatar: ImageVariant = ImageVariantFactory(
        owner=user,
        file__filename="avatar-1200.webp",
        role="avatar__original_format",
        width=1200,
        height=1200,
    )

    response: Response = api_client.get(reverse("users:profile-profile"), {"size": "640"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["avatar"]["fallback_image"]["url"] == default_avatar.file.url
    assert response.data["avatar"]["fallback_image"]["url"] != requested_avatar.file.url


@pytest.mark.django_db
def test_profile_avatar_returns_empty_candidates_when_variant_missing(
    api_client: APIClient,
) -> None:
    """Integration: profile endpoint depends on generated variants."""
    user: PortfolioUser = UserFactory(avatar=jpeg_field("photo_legacy.jpg", size=(800, 800)))
    process_image_task("users", "User", user.pk, ["avatar"])
    user.variants.all().delete()

    url: str = reverse("users:profile-profile")
    response: Response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["avatar"] == {
        "fallback_image": None,
        "variants": {"original_format": []},
    }
