# backend/users/models.py
import logging
from typing import Optional

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# Django limitation: AbstractUser's default manager expects 'username' parameter.
# We MUST override create_superuser to accept 'email' for createsuperuser command to work.
class UserManager(BaseUserManager):
    def create_superuser(
        self, email: str, password: Optional[str] = None, **extra_fields: dict
    ) -> "User":
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

    short_description = models.TextField(
        blank=True,
        help_text=_(
            "Hero section text. Split by the first period ('.'): "
            "the first segment will be large/bold, following text will be smaller."
        ),
    )
    bio = models.TextField(max_length=10000, blank=True, help_text="General/Global bio about you")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    about_me_image = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    about_me_image2 = models.ImageField(upload_to="about_me_images/", null=True, blank=True)

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


class Profile(models.Model):
    """
    Model representing different niche profiles for the same user.
    Enables specific content for different personas (Programming, Astrophotography).
    """

    class ProfileType(models.TextChoices):
        PROGRAMMING = "PROGRAMMING", _("Programming")
        ASTRO = "ASTRO", _("Astrophotography")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profiles")
    type = models.CharField(
        max_length=20,
        choices=ProfileType.choices,
        unique=True,
        help_text="The niche this profile represents",
    )
    is_active = models.BooleanField(default=True)

    title = models.CharField(max_length=255, help_text="Public title, e.g. 'Software Engineer'")
    specific_bio = models.TextField(help_text="Persona-specific bio/description")

    # Persona-specific links
    github_url = models.URLField(max_length=200, blank=True)
    linkedin_url = models.URLField(max_length=200, blank=True)
    astrobin_url = models.URLField(
        max_length=200,
        blank=True,
        help_text="Link to your Astrobin profile",
    )
    fb_url = models.URLField(max_length=200, blank=True)
    ig_url = models.URLField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["type"]

    def __str__(self) -> str:
        return f"{self.get_type_display()} Profile"
