# backend/users/models.py
import logging
from typing import Any, Optional, cast

from django_ckeditor_5.fields import CKEditor5Field
from model_utils import FieldTracker
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericRelation
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy as _

from common.types import ImageVariantSource, ImageVariantSpec, ViewportWidths
from common.utils.image import get_available_image_url
from core.mixins import ImageVariantModelMixin
from core.models import ImageVariant, SingletonModel
from core.tasks import process_image_task
from translation.mixins import AutomatedTranslationModelMixin

logger = logging.getLogger(__name__)

USER_IMAGE_FIELD_MAPPINGS: dict[str, dict[str, str]] = {
    "avatar": {
        "cropped": "avatar_cropped",
    },
    "about_me_image": {
        "cropped": "about_me_image_cropped",
    },
    "about_me_image2": {
        "cropped": "about_me_image2_cropped",
    },
}


# Django limitation: AbstractUser's default manager expects 'username' parameter.
# We MUST override create_superuser to accept 'email' for createsuperuser command to work.
class UserManager(TranslatableManager, BaseUserManager):
    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
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


class User(
    ImageVariantModelMixin,
    AutomatedTranslationModelMixin,
    TranslatableModel,
    AbstractUser,
    SingletonModel,
):
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
    image_variant_specs = (
        ImageVariantSpec(
            role="original_format",
            viewport_widths=ViewportWidths.fixed(2560),
            quality=35,
            label="Profile image display candidate",
        ),
    )

    username = None  # type: ignore[assignment]  # Remove username field - use email instead
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    contact_email = models.EmailField(
        blank=True, help_text="Public contact email displayed in footer"
    )
    image_tracker = FieldTracker(
        fields=[
            "avatar",
            "avatar_cropped",
            "about_me_image",
            "about_me_image_cropped",
            "about_me_image2",
            "about_me_image2_cropped",
        ]
    )

    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    avatar_cropped = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name=_("Avatar cropped"),
        help_text=_("Cropped avatar managed by the admin cropper."),
    )
    about_me_image = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    about_me_image_cropped = models.ImageField(
        upload_to="about_me_images/",
        null=True,
        blank=True,
        verbose_name=_("About Me Image cropped"),
        help_text=_("Cropped portrait managed by the admin cropper."),
    )
    about_me_image2 = models.ImageField(upload_to="about_me_images/", null=True, blank=True)
    about_me_image2_cropped = models.ImageField(
        upload_to="about_me_images/",
        null=True,
        blank=True,
        verbose_name=_("About Me Image 2 cropped"),
        help_text=_("Cropped portrait managed by the admin cropper."),
    )
    variants = GenericRelation(
        ImageVariant,
        content_type_field="content_type",
        object_id_field="object_id",
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
            changed_image_fields: list[str] = []
            for field_name, variants in USER_IMAGE_FIELD_MAPPINGS.items():
                source_changed: bool = self.image_tracker.has_changed(field_name)
                cropped_changed: bool = self.image_tracker.has_changed(variants["cropped"])
                if source_changed and not cropped_changed:
                    setattr(self, variants["cropped"], None)
                if source_changed or cropped_changed:
                    changed_image_fields.append(field_name)

            self.clean()
            super().save(*args, **kwargs)

            if changed_image_fields and not kwargs.get("update_fields"):
                process_image_task.delay_on_commit(
                    self._meta.app_label,
                    self._meta.model_name,
                    self.pk,
                    changed_image_fields,
                )

            update_fields = kwargs.get("update_fields")
            if not update_fields or any(
                field in update_fields for field in self.translation_trigger_fields
            ):
                self.trigger_translations()
        except IntegrityError as exc:
            raise ValueError("Failed to save user. Only one user is allowed.") from exc

    def get_effective_image_field(self, source_field_name: str) -> Any:
        cropped_field_name = USER_IMAGE_FIELD_MAPPINGS[source_field_name]["cropped"]
        cropped_field = getattr(self, cropped_field_name)
        if cropped_field:
            return cropped_field
        return getattr(self, source_field_name)

    def get_serving_image_url(self, source_field_name: str) -> str:
        """Return the generated original_format URL with a source-image safety fallback."""
        effective_source_field: Any = self.get_effective_image_field(source_field_name)
        source_width = effective_source_field.width if effective_source_field else None
        serving_field = (
            self.get_variant_file(
                "original_format",
                source_width,
                source_name=source_field_name,
            )
            if source_width
            else None
        )
        if serving_field:
            try:
                return str(serving_field.url)
            except ValueError:
                pass

        source_url = get_available_image_url(effective_source_field)
        if source_url:
            logger.warning(
                "Falling back to source image because original_format variant is missing",
                extra={
                    "model": self._meta.label,
                    "pk": str(self.pk),
                    "source_field_name": source_field_name,
                },
            )
        return source_url

    # Domain Logic Methods

    def get_full_name(self) -> str:
        """Get full name or email."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return self.email

    def get_avatar_url(self) -> str:
        """Get avatar URL or default placeholder."""
        url = self.get_serving_image_url("avatar")
        if not url:
            return "/static/images/default-avatar.png"

        if not self.updated_at:
            return url

        separator = "&" if "?" in url else "?"
        return f"{url}{separator}v={int(self.updated_at.timestamp())}"

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

    def get_image_variant_sources(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageVariantSource]:
        field_names = changed_field_names or list(USER_IMAGE_FIELD_MAPPINGS.keys())
        sources: list[ImageVariantSource] = []
        for field_name in field_names:
            if field_name not in USER_IMAGE_FIELD_MAPPINGS:
                continue
            upload_dir = "avatars" if field_name == "avatar" else "about_me_images"
            sources.append(
                ImageVariantSource(
                    field_name=field_name,
                    source_image=self.get_effective_image_field(field_name),
                    upload_dir=upload_dir,
                    role_namespace=field_name,
                )
            )
        return sources


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
