"""Default shop content used by the ``configure_shop`` management command."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shop.models import ShopSettings


@dataclass(frozen=True)
class ShopSettingsSeedContent:
    """Default translated copy for the singleton ``ShopSettings`` record."""

    title: str
    description: str


SHOP_SETTINGS_DEFAULTS: dict[str, ShopSettingsSeedContent] = {
    "en": ShopSettingsSeedContent(
        title="Collect the night sky in print.",
        description=(
            "<p>Discover selected astrophotography images and some of my best work, "
            "presented here as fine art prints available for purchase.</p>"
        ),
    ),
    "pl": ShopSettingsSeedContent(
        title="Zabierz nocne niebo na swoją ścianę.",
        description=(
            "<p>Odkryj wybrane zdjęcia astrofotograficzne oraz niektóre z moich najlepszych prac,"
            "— dostępne tutaj jako wydruki do kupienia.</p>"
        ),
    ),
}


def seed_shop_settings_defaults(
    shop_settings: "ShopSettings",
    *,
    overwrite: bool = False,
) -> dict[str, bool]:
    """Seed translated shop title/description defaults into an existing settings record.

    Returns a language->changed mapping so callers can report what happened.
    """

    changed_by_language: dict[str, bool] = {}

    for language_code, default_content in SHOP_SETTINGS_DEFAULTS.items():
        shop_settings.set_current_language(language_code)
        translation = shop_settings.translations.filter(language_code=language_code).first()

        current_title = (getattr(translation, "title", "") or "").strip()
        current_description = (getattr(translation, "description", "") or "").strip()

        should_update = overwrite or not current_title or not current_description
        changed_by_language[language_code] = should_update

        if not should_update:
            continue

        if overwrite or not current_title:
            shop_settings.title = default_content.title

        if overwrite or not current_description:
            shop_settings.description = default_content.description

        shop_settings.save()

    return changed_by_language


def get_or_create_shop_settings(
    shop_settings: "ShopSettings | None" = None,
) -> tuple["ShopSettings", bool]:
    """Return the provided singleton instance or load/create the persisted one."""
    if shop_settings is not None:
        return shop_settings, False

    from shop.models import ShopSettings

    return ShopSettings.get_or_create_current()
