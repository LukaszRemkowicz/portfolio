# backend/users/tests/test_models.py
"""
Tests for users models
"""

import pytest
from pytest_mock import MockerFixture

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from common.utils.image import ImageSpec
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
def test_user_singleton_pattern_only_one_user_allowed() -> None:
    """Test that only one user can exist (singleton pattern)"""
    # Create first user - should succeed
    UserFactory.create_superuser()
    assert User.objects.count() == 1

    # Try to create second user - should raise ValueError
    second_user = UserFactory.build()
    with pytest.raises(ValueError, match="Only one user is allowed"):
        second_user.save()

    # Verify only one user still exists
    assert User.objects.count() == 1
    assert User.objects.first().email == "admin@example.com"


@pytest.mark.django_db
def test_user_get_user_method() -> None:
    """Test User.get_user() classmethod returns the singleton user"""
    # No user exists yet
    assert User.get_user() is None

    # Create user
    user = UserFactory.create_superuser()

    # get_user() should return the user
    retrieved_user = User.get_user()
    assert retrieved_user is not None
    assert retrieved_user.email == user.email
    assert retrieved_user.id == user.id


@pytest.mark.django_db
def test_user_manager_create_superuser() -> None:
    """Test creating a superuser via UserManager"""
    email = "admin@example.com"
    password = "password123"
    user = User.objects.create_superuser(email=email, password=password)

    assert user.email == email
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.check_password(password) is True


@pytest.mark.django_db
def test_user_manager_create_superuser_missing_email() -> None:
    """Test that create_superuser raises error if email is missing"""
    with pytest.raises(ValueError, match="Email must be set"):
        User.objects.create_superuser(email="", password="password123")


@pytest.mark.django_db
def test_user_str_method() -> None:
    """Test User.__str__ method"""
    email = "test@example.com"
    user = UserFactory.build(email=email)
    assert str(user) == email


@pytest.mark.django_db
def test_user_save_integrity_error(mocker: MockerFixture) -> None:
    """Test handling of IntegrityError in User.save()"""
    user = UserFactory.build(email="test@example.com")
    mock_save = mocker.patch("django.db.models.Model.save")
    mock_save.side_effect = IntegrityError("Duplicate entry")
    with pytest.raises(ValueError, match="Failed to save user. Only one user is allowed."):
        user.save()


@pytest.mark.django_db
def test_user_save_generic_exception(mocker: MockerFixture) -> None:
    """Test handling of generic Exception in User.save()"""
    user = UserFactory.build(email="test@example.com")
    mock_save = mocker.patch("django.db.models.Model.save")
    mock_save.side_effect = Exception("Some other error")
    with pytest.raises(Exception, match="Some other error"):
        user.save()


@pytest.mark.django_db
class TestUserDomainMethods:
    """Tests for User domain logic methods."""

    def test_get_full_name_with_both_names(self):
        """Test get_full_name returns first + last name."""
        user = UserFactory.create_superuser(
            email="test@example.com", first_name="John", last_name="Doe"
        )
        assert user.get_full_name() == "John Doe"

    def test_get_full_name_with_only_first_name(self):
        """Test get_full_name returns first name only."""
        user = UserFactory.create_superuser(
            email="test@example.com", first_name="John", last_name=""
        )
        assert user.get_full_name() == "John"

    def test_get_full_name_fallback_to_email(self):
        """Test get_full_name falls back to email."""
        user = UserFactory.create_superuser(email="test@example.com", first_name="", last_name="")
        assert user.get_full_name() == "test@example.com"

    def test_display_name_property(self):
        """Test display_name property works."""
        user = UserFactory.create_superuser(
            email="test@example.com", first_name="John", last_name=""
        )
        assert user.display_name == "John"

    def test_get_avatar_url_with_no_avatar(self):
        """Test get_avatar_url returns placeholder when no avatar."""
        user = UserFactory.create_superuser(email="test@example.com")
        url = user.get_avatar_url()
        assert url == "/static/images/default-avatar.png"

    def test_get_avatar_url_appends_version_for_admin_cache_busting(self):
        """Jazzmin sidebar avatar should get a versioned URL after avatar updates."""
        user = UserFactory.build(email="test@example.com")
        user.avatar.name = "avatars/avatar.jpg"
        user.updated_at = timezone.now()

        url = user.get_avatar_url()

        assert url.startswith("/media/avatars/avatar.jpg")
        assert "?v=" in url

    def test_has_complete_profile_false_missing_fields(self):
        """Test has_complete_profile returns False when incomplete."""
        user = UserFactory.create_superuser(email="test@example.com", bio="")
        assert user.has_complete_profile() is False

    def test_get_avatar_spec(self):
        """Test that get_avatar_spec returns the correct spec from settings."""
        user = UserFactory.build()
        spec = user.get_avatar_spec()
        assert isinstance(spec, ImageSpec)
        assert spec == settings.IMAGE_OPTIMIZATION_SPECS["AVATAR"]

    def test_get_portrait_spec(self):
        """Test that get_portrait_spec returns the correct spec from settings."""
        user = UserFactory.build()
        spec = user.get_portrait_spec()
        assert isinstance(spec, ImageSpec)
        assert spec == settings.IMAGE_OPTIMIZATION_SPECS["PORTRAIT"]
