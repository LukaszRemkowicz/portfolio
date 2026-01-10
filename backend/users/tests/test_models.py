# backend/users/tests/test_models.py
"""
Tests for users models
"""

import pytest
from typing import List
from datetime import datetime, timedelta

from django.utils import timezone

from users.models import User, UserLoginAttempts


@pytest.mark.django_db
def test_user_login_attempts_creation():
    """Test that UserLoginAttempts can be created with datetime and counter"""
    attempted_at: datetime = timezone.now()
    attempt: UserLoginAttempts = UserLoginAttempts.objects.create(
        attempted_at=attempted_at,
        counter=1,
    )
    
    assert attempt.id is not None
    assert attempt.attempted_at == attempted_at
    assert attempt.counter == 1


@pytest.mark.django_db
def test_user_login_attempts_counter_increments():
    """Test that counter field can be incremented"""
    attempt: UserLoginAttempts = UserLoginAttempts.objects.create(
        attempted_at=timezone.now(),
        counter=1,
    )
    
    attempt.counter = 5
    attempt.save()
    
    assert attempt.counter == 5


@pytest.mark.django_db
def test_user_login_attempts_ordering():
    """Test that UserLoginAttempts can be ordered by datetime"""
    first_attempt: UserLoginAttempts = UserLoginAttempts.objects.create(
        attempted_at=timezone.now() - timedelta(hours=1),
        counter=1,
    )
    second_attempt: UserLoginAttempts = UserLoginAttempts.objects.create(
        attempted_at=timezone.now(),
        counter=1,
    )
    
    attempts: List[UserLoginAttempts] = list(UserLoginAttempts.objects.all().order_by("attempted_at"))
    
    assert attempts[0].id == first_attempt.id
    assert attempts[1].id == second_attempt.id


@pytest.mark.django_db
def test_user_singleton_pattern_only_one_user_allowed() -> None:
    """Test that only one user can exist (singleton pattern)"""
    # Create first user - should succeed
    first_user = User(email="first@example.com", first_name="First", is_active=True)
    first_user.set_password("password123")
    first_user.save()
    assert User.objects.count() == 1
    
    # Try to create second user - should raise ValueError
    second_user = User(email="second@example.com", first_name="Second", is_active=True)
    second_user.set_password("password123")
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
    user = User(email="test@example.com", first_name="Test", is_active=True)
    user.set_password("password123")
    user.save()
    
    # get_user() should return the user
    retrieved_user = User.get_user()
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.id == user.id
