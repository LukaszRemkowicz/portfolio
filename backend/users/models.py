# backend/users/models.py
import logging
from typing import Any, Optional, cast

from django_ckeditor_5.fields import CKEditor5Field
from model_utils import FieldTracker
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext_lazy as _

from common.utils.image import convert_to_webp
from core.models import LandingPageSettings, SingletonModel
from translation.mixins import AutomatedTranslationModelMixin
from users.tasks import process_user_images_task

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

    # Avatar and about_me images are visible but not portfolio photography —
    # 35% quality gives good fidelity at significantly smaller file sizes.
    webp_quality: int = 35

    username = None  # type: ignore[assignment]  # Remove username field - use email instead
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    contact_email = models.EmailField(
        blank=True, help_text="Public contact email displayed in footer"
    )
    image_tracker = FieldTracker(fields=["avatar", "about_me_image", "about_me_image2"])

    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    avatar_legacy = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Legacy Avatar"),
        help_text=_("Original avatar before WebP conversion. Used for rollback."),
    )
    about_me_image = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    about_me_image_legacy = models.ImageField(
        upload_to="about_me_images/",
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Legacy About Me Image"),
        help_text=_(
            "Original about_me_image before WebP conversion. Used for rollback. "
            "TODO: Will be removed in future versions."
        ),
    )
    about_me_image2 = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    about_me_image2_legacy = models.ImageField(
        upload_to="about_me_images/",
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Legacy About Me Image 2"),
        help_text=_(
            "Original about_me_image2 before WebP conversion. Used for rollback. "
            "TODO: Will be removed in future versions."
        ),
    )

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
        """Enforce singleton on save and trigger translations/image processing"""
        try:
            changed_image_fields = []
            for field_name in ["avatar", "about_me_image", "about_me_image2"]:
                if self.image_tracker.has_changed(field_name):
                    changed_image_fields.append(field_name)

            self.clean()
            super().save(*args, **kwargs)

            if changed_image_fields and not kwargs.get("update_fields"):
                transaction.on_commit(
                    lambda: process_user_images_task.delay(self.pk, changed_image_fields)
                )

            self.trigger_translations()
        except IntegrityError as exc:
            raise ValueError("Failed to save user. Only one user is allowed.") from exc

    def _convert_image_field_to_webp(
        self, field_name: str, legacy_field_name: str, max_dimension: int, quality: int
    ) -> None:
        """Convert a single ImageField to WebP and store the original as legacy."""
        field: Any = getattr(self, field_name)
        result: tuple[str, Any] | None = convert_to_webp(
            field, quality=quality, max_dimension=max_dimension
        )
        if result is None:
            setattr(self, legacy_field_name, None)
            return
        original_name, webp_content = result
        setattr(self, legacy_field_name, original_name)
        field.save(webp_content.name, webp_content, save=False)

    def _get_serving_image_url(self, field_name: str, legacy_field_name: str) -> str:
        """Return the URL of the field to serve based on the Admin serve_webp_images toggle."""
        settings_obj: LandingPageSettings | None = LandingPageSettings.get_current()
        if settings_obj and settings_obj.serve_webp_images:
            serving_field = getattr(self, field_name)
        else:
            serving_field = getattr(self, legacy_field_name) or getattr(self, field_name)
        if serving_field:
            try:
                return str(serving_field.url)
            except ValueError:
                pass
        return ""

    # Domain Logic Methods

    def get_full_name(self) -> str:
        """Get full name or email."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.email

    def get_avatar_url(self) -> str:
        """Get avatar URL or default placeholder."""
        url = self._get_serving_image_url("avatar", "avatar_legacy")
        return url if url else "/static/images/default-avatar.png"

    def has_complete_profile(self) -> bool:
        """Check if user has completed their profile."""
        # Check if user has bio in default language
        bio = self.safe_translation_getter("bio", any_language=False)
        short_desc = self.safe_translation_getter("short_description", any_language=False)

        return all(
            [
                self.first_name,
                self.last_name,
                bio,
                short_desc,
                self.avatar,
            ]
        )

    @property
    def display_name(self) -> str:
        """Alias for get_full_name() for template convenience."""
        return self.get_full_name()


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

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        self.trigger_translations()

    def __str__(self) -> str:
        return f"{self.get_type_display()} - {self.title}"
