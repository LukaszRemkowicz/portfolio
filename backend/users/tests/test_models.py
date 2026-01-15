# backend/users/tests/test_models.py
"""
Tests for users models
"""

from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.db import IntegrityError

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
    assert str(profile) == "Programming Profile"


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
    UserFactory(email="first@example.com", first_name="First")
    assert User.objects.count() == 1

    # Try to create second user - should raise ValueError
    # We use build() then save() to trigger the model's clean/save logic manually
    # or just another Factory call which calls save()
    second_user = UserFactory.build(email="second@example.com", first_name="Second")
    with pytest.raises(ValueError, match="Only one user is allowed"):
        second_user.save()

    # Verify only one user still exists
    assert User.objects.count() == 1
    assert User.objects.first().email == "first@example.com"


@pytest.mark.django_db
def test_user_get_user_method() -> None:
    """Test User.get_user() classmethod returns the singleton user"""
    # No user exists yet
    assert User.get_user() is None

    # Create user
    user = UserFactory(email="test@example.com", first_name="Test")

    # get_user() should return the user
    retrieved_user = User.get_user()
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
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
def test_user_save_integrity_error() -> None:
    """Test handling of IntegrityError in User.save()"""
    user = UserFactory.build(email="test@example.com")
    with patch("django.db.models.Model.save") as mock_save:
        mock_save.side_effect = IntegrityError("Duplicate entry")
        with pytest.raises(ValueError, match="Failed to save user. Only one user is allowed."):
            user.save()


@pytest.mark.django_db
def test_user_save_generic_exception() -> None:
    """Test handling of generic Exception in User.save()"""
    user = UserFactory.build(email="test@example.com")
    with patch("django.db.models.Model.save") as mock_save:
        mock_save.side_effect = Exception("Some other error")
        with pytest.raises(Exception, match="Some other error"):
            user.save()
