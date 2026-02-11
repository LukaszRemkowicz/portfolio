# backend/users/models.py
import logging
from typing import Any, Optional, cast

from django_ckeditor_5.fields import CKEditor5Field
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy as _

from core.models import SingletonModel
from translation.mixins import AutomatedTranslationModelMixin

logger = logging.getLogger(__name__)


# Django limitation: AbstractUser's default manager expects 'username' parameter.
# We MUST override create_superuser to accept 'email' for createsuperuser command to work.
class UserManager(TranslatableManager, BaseUserManager):
    def create_superuser(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = cast(User, self.model(email=email, **extra_fields))
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AutomatedTranslationModelMixin, TranslatableModel, AbstractUser, SingletonModel):
    """
    Custom user model with email as username.
    Singleton pattern: Only one user instance is allowed in the database.
    """

    # Translation trigger fields
    translation_service_method = "translate_user"
    translation_trigger_fields = ["short_description", "bio"]

    username = None  # type: ignore[assignment]  # Remove username field - use email instead
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    contact_email = models.EmailField(
        blank=True, help_text="Public contact email displayed in footer"
    )
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    about_me_image = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    about_me_image2 = models.ImageField(upload_to="about_me_images/", null=True, blank=True)

    translations = TranslatedFields(
        short_description=models.TextField(
            blank=True,
            help_text=_(
                "Hero section text. Split by the first period ('.'): "
                "the first segment will be large/bold, following text will be smaller."
            ),
        ),
        bio=CKEditor5Field(_("Bio"), config_name="extends", blank=True),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return self.email

    @classmethod
    def get_user(cls) -> Optional["User"]:
        """Return the main portfolio user"""
        return cls.objects.first()

    def clean(self) -> None:
        """Ensure singleton pattern by preventing addition of multiple users"""
        if not self.pk and User.objects.exists():
            raise ValueError("Only one user is allowed.")
        super().clean()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Enforce singleton on save and trigger translations"""
        try:
            self.clean()
            super().save(*args, **kwargs)
            self.trigger_translations()
        except IntegrityError as exc:
            raise ValueError("Failed to save user. Only one user is allowed.") from exc


class Profile(AutomatedTranslationModelMixin, TranslatableModel):
    """Admin interface for managing different user profiles"""

    # Translation trigger fields
    translation_service_method = "translate_profile"
    translation_trigger_fields = ["title", "specific_bio"]

    class ProfileType(models.TextChoices):
        PROGRAMMING = "PROGRAMMING", _("Programming Profile")
        ASTRO = "ASTRO", _("Astrophotography Profile")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profiles")
    type = models.CharField(
        max_length=20, choices=ProfileType.choices, default=ProfileType.PROGRAMMING
    )
    is_active = models.BooleanField(default=True)

    translations = TranslatedFields(
        title=models.CharField(max_length=255, blank=True),
        specific_bio=models.TextField(blank=True),
    )

    github_url = models.URLField(blank=True, verbose_name="GitHub URL")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    astrobin_url = models.URLField(blank=True, verbose_name="AstroBin URL")
    fb_url = models.URLField(blank=True, verbose_name="Facebook URL")
    ig_url = models.URLField(blank=True, verbose_name="Instagram URL")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TranslatableManager()

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
        unique_together = ("user", "type")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.trigger_translations()

    def __str__(self) -> str:
        return f"{self.get_type_display()} - {self.title}"
