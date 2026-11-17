from unittest.mock import patch

import pytest
from axes.models import AccessAttempt, AccessFailureLog, AccessLog

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse

from astrophotography.models import MeteorsMainPageConfig
from astrophotography.tests.factories import (
    AstroImageFactory,
    CameraFactory,
    LensFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    MeteorsMainPageConfigFactory,
    PlaceFactory,
    TagFactory,
    TelescopeFactory,
    TrackerFactory,
    TripodFactory,
)
from core.tests.factories import (
    ImageVariantFactory,
    LandingPageSettingsFactory,
    TranslationTaskFactory,
)
from inbox.tests.factories import ContactMessageFactory
from programming.tests.factories import ProjectFactory, ProjectImageFactory
from shop.models import ShopSettings
from shop.tests.factories import ShopProductFactory
from users.tests.factories import ProfileFactory


@pytest.mark.django_db
def test_every_registered_admin_add_and_change_page(admin_client, admin_user):
    factories = {
        "axes.AccessAttempt": lambda: AccessAttempt.objects.create(failures_since_start=1),
        "axes.AccessFailureLog": AccessFailureLog.objects.create,
        "axes.AccessLog": AccessLog.objects.create,
        "auth.Group": lambda: Group.objects.create(name="Smoke group"),
        "astrophotography.AstroImage": AstroImageFactory,
        "astrophotography.Camera": CameraFactory,
        "astrophotography.Lens": LensFactory,
        "astrophotography.MainPageBackgroundImage": MainPageBackgroundImageFactory,
        "astrophotography.MainPageLocation": MainPageLocationFactory,
        "astrophotography.MeteorsMainPageConfig": lambda: (
            MeteorsMainPageConfig.objects.first() or MeteorsMainPageConfigFactory()
        ),
        "astrophotography.Place": PlaceFactory,
        "astrophotography.Tag": TagFactory,
        "astrophotography.Telescope": TelescopeFactory,
        "astrophotography.Tracker": TrackerFactory,
        "astrophotography.Tripod": TripodFactory,
        "core.ImageVariant": ImageVariantFactory,
        "core.LandingPageSettings": lambda: LandingPageSettingsFactory(
            meteors=MeteorsMainPageConfig.objects.first() or MeteorsMainPageConfigFactory()
        ),
        "inbox.ContactMessage": ContactMessageFactory,
        "programming.Project": ProjectFactory,
        "programming.ProjectImage": ProjectImageFactory,
        "shop.ShopProduct": ShopProductFactory,
        "shop.ShopSettings": lambda: ShopSettings.objects.create(title="Smoke shop"),
        "translation.TranslationTask": lambda: TranslationTaskFactory(
            content_type=ContentType.objects.get_for_model(admin_user), object_id=str(admin_user.pk)
        ),
        "users.Profile": ProfileFactory,
        "users.User": lambda: admin_user,
    }
    assert {model._meta.label for model in admin.site._registry} == set(factories)
    request = RequestFactory().get("/")
    request.user = admin_user
    with patch("core.models.submit"):
        for model, model_admin in admin.site._registry.items():
            obj = factories[model._meta.label]()
            prefix = f"admin:{model._meta.app_label}_{model._meta.model_name}"
            for view, args, allowed in (
                ("add", (), model_admin.has_add_permission(request)),
                ("change", (obj.pk,), model_admin.has_view_or_change_permission(request, obj)),
            ):
                response = admin_client.get(reverse(f"{prefix}_{view}", args=args))
                assert response.status_code == (200 if allowed else 403), (
                    model._meta.label,
                    view,
                    response.status_code,
                )
