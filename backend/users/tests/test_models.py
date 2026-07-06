# backend/users/tests/test_models.py
"""
Tests for users models
"""

import pytest
from pytest_mock import MockerFixture

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from common.tests.image_helpers import jpeg_field, png_field
from users.models import Profile
from users.tests.factories import ProgrammingProfileFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
def test_profile_creation(user: User):
    """Test that Profile can be created correctly"""
    profile = ProgrammingProfileFactory(user=user)

    assert profile.id is not None
    assert profile.user == user
    assert profile.type == Profile.ProfileType.PROGRAMMING
    assert profile.title == "Dev"
    assert str(profile) == "Programming Profile - Dev"


@pytest.mark.django_db
def test_profile_type_uniqueness(user: User):
    """Test that a user cannot have duplicate profile types"""
    ProgrammingProfileFactory(user=user)

    with pytest.raises(IntegrityError):
        ProgrammingProfileFactory(user=user)


@pytest.mark.django_db
def test_user_singleton_pattern_only_one_user_allowed(superuser: User) -> None:
    """Test that only one user can exist (singleton pattern)"""
    # First user exists through the singleton admin fixture.
    assert User.objects.count() == 1

    # Try to create second user - should raise ValueError
    second_user = UserFactory.build()
    with pytest.raises(ValueError, match="Only one user is allowed"):
        second_user.save()

    # Verify only one user still exists
    assert User.objects.count() == 1
    assert User.objects.first() == superuser


@pytest.mark.django_db
def test_user_get_user_method() -> None:
    """Test User.get_user() classmethod returns the singleton user"""
    # No user exists yet
    assert User.get_user() is None

    # Create user
    created_user: User = UserFactory.create_superuser()

    # get_user() should return the user
    retrieved_user = User.get_user()
    assert retrieved_user is not None
    assert retrieved_user.email == created_user.email
    assert retrieved_user.id == created_user.id


@pytest.mark.django_db
def test_user_manager_create_superuser() -> None:
    """Test creating a superuser via UserManager"""
    email = "admin@example.com"
    password = "password123"
    created_superuser = User.objects.create_superuser(email=email, password=password)

    assert created_superuser.email == email
    assert created_superuser.is_staff is True
    assert created_superuser.is_superuser is True
    assert created_superuser.check_password(password) is True


@pytest.mark.django_db
def test_user_manager_create_superuser_missing_email() -> None:
    """Test that create_superuser raises error if email is missing"""
    with pytest.raises(ValueError, match="Email must be set"):
        User.objects.create_superuser(email="", password="password123")


@pytest.mark.django_db
def test_user_str_method(user: User) -> None:
    """Test User.__str__ method"""
    assert str(user) == user.email


@pytest.mark.django_db
def test_user_save_integrity_error(user: User, mocker: MockerFixture) -> None:
    """Test handling of IntegrityError in User.save()"""
    mock_save = mocker.patch("django.db.models.Model.save")
    mock_save.side_effect = IntegrityError("Duplicate entry")
    with pytest.raises(ValueError, match="Failed to save user. Only one user is allowed."):
        user.save()


@pytest.mark.django_db
def test_user_save_generic_exception(user: User, mocker: MockerFixture) -> None:
    """Test handling of generic Exception in User.save()"""
    mock_save = mocker.patch("django.db.models.Model.save")
    mock_save.side_effect = Exception("Some other error")
    with pytest.raises(Exception, match="Some other error"):
        user.save()


@pytest.mark.django_db
class TestUserDomainMethods:
    """Tests for User domain logic methods."""

    def test_get_full_name_with_both_names(self, user: User):
        """Test get_full_name returns first + last name."""
        user.first_name = "John"
        user.last_name = "Doe"
        assert user.get_full_name() == "John Doe"

    def test_get_full_name_with_only_first_name(self, user: User):
        """Test get_full_name returns first name only."""
        user.first_name = "John"
        user.last_name = ""
        assert user.get_full_name() == "John"

    def test_get_full_name_fallback_to_email(self, user: User):
        """Test get_full_name falls back to email."""
        user.email = "test@example.com"
        user.first_name = ""
        user.last_name = ""
        assert user.get_full_name() == user.email

    def test_display_name_property(self, user: User):
        """Test display_name property works."""
        user.first_name = "John"
        user.last_name = ""
        assert user.display_name == "John"

    def test_get_avatar_url_with_no_avatar(self, user: User):
        """Test get_avatar_url returns placeholder when no avatar."""
        url = user.get_avatar_url()
        assert url == "/static/images/default-avatar.png"

    def test_get_avatar_url_appends_version_for_admin_cache_busting(
        self, user: User, mocker: MockerFixture
    ):
        """Jazzmin sidebar avatar should get a versioned URL after avatar updates."""
        user.updated_at = timezone.now()
        mocker.patch.object(user, "get_serving_image_url", return_value="/media/avatars/avatar.jpg")

        url = user.get_avatar_url()

        assert url.startswith("/media/avatars/avatar.jpg")
        assert "?v=" in url

    def test_has_complete_profile_false_missing_fields(self, user: User):
        """Test has_complete_profile returns False when incomplete."""
        user.bio = ""
        assert user.has_complete_profile() is False


@pytest.mark.django_db
def test_user_save_clears_stale_cropped_file_when_original_changes(superuser: User):
    superuser.avatar = jpeg_field("avatar-original.jpg")
    superuser.avatar_cropped = png_field("avatar-cropped.png", size=(280, 280))
    superuser.save()

    superuser.avatar = jpeg_field("avatar-replacement.jpg")
    superuser.save()
    superuser.refresh_from_db()

    assert "avatar-replacement" in superuser.avatar.name
    assert not superuser.avatar_cropped
