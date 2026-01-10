# backend/users/models.py
import logging
from typing import Optional

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import IntegrityError, models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# Django limitation: AbstractUser's default manager expects 'username' parameter.
# We MUST override create_superuser to accept 'email' for createsuperuser command to work.
class UserManager(BaseUserManager):
    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields: dict) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    """
    Custom user model with email as username.
    Singleton pattern: Only one user instance is allowed in the database.
    """

    username = None  # Remove username field - use email instead
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

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

    objects = UserManager()  # Required for createsuperuser command to work with email

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email

    @classmethod
    def get_user(cls) -> Optional["User"]:
        """Get the singleton user instance, or None if it doesn't exist."""
        return cls.objects.first()

    def save(self, *args: tuple, **kwargs: dict) -> None:
        """
        Override save to enforce singleton pattern.
        Only one user is allowed - if creating, ensure no other user exists.
        """
        # If this is a new user (no pk) and another user already exists, raise error
        if self.pk is None and type(self).objects.exists():
            existing_user = type(self).objects.first()
            raise ValueError(
                f"Only one user is allowed. User already exists: {existing_user.email}. "
                "Update the existing user instead."
            )
        
        try:
            super().save(*args, **kwargs)
        except IntegrityError as error:
            # Handle potential integrity errors (e.g., duplicate email or singleton constraint)
            logger.error(f"Failed to save User due to IntegrityError: {error}")
            raise ValueError(
                "Failed to save user. Only one user is allowed. "
                "If updating, ensure you're editing the existing user."
            ) from error
        except Exception as error:
            logger.error(f"Failed to save User: {error}")
            raise


class UserLoginAttempts(models.Model):
    """
    Model to track user login attempts for bot/brute force protection.
    Stores datetime and counter for login attempts.
    """

    attempted_at = models.DateTimeField(
        default=timezone.now,
        help_text="Datetime when the login attempt occurred",
    )
    counter = models.IntegerField(
        default=1,
        help_text="Number of login attempts (counter)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Login Attempt"
        verbose_name_plural = "User Login Attempts"
        ordering = ["-attempted_at"]

    def __str__(self) -> str:
        return f"Login Attempt at {self.attempted_at} (counter: {self.counter})"
