import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from jazzmin.templatetags.jazzmin import get_side_menu

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.contenttypes.models import ContentType
from django.template import Context
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from astrophotography.tests.factories import AstroImageFactory
from core.admin import ImageVariantAdmin, ImageVariantAstroImageFilterForm
from core.models import ImageVariant
from core.widgets import ThemedModelSelect2Widget


def test_image_variant_is_visible_in_astrophotography_admin_ordering() -> None:
    astrophotography_section = next(
        section
        for section in settings.ADMIN_SITE_ORDERING
        if section["app"] == "astrophotography" and section["label"] == "Astrophotography"
    )

    assert "core.ImageVariant" in astrophotography_section["models"]


def test_image_variant_uses_astrophotography_image_icon_in_sidebar() -> None:
    menu = get_side_menu(
        Context(
            {
                "user": object(),
                "available_apps": [
                    {
                        "app_label": "astrophotography",
                        "name": "Astrophotography",
                        "models": [
                            {
                                "object_name": "ImageVariant",
                                "admin_url": "/admin/core/imagevariant/",
                            }
                        ],
                    }
                ],
            }
        )
    )

    assert menu[0]["models"][0]["icon"] == "fas fa-image"


def test_image_variant_admin_list_columns_are_compact() -> None:
    admin_instance = ImageVariantAdmin(ImageVariant, AdminSite())

    assert admin_instance.get_list_display(request=None) == (
        "order_number",
        "filename",
        "role",
        "dimensions",
        "mime_type",
    )
    assert admin_instance.list_display_links == ("order_number", "filename")
    assert admin_instance.ordering == ("-created_at", "-id")


def test_image_variant_admin_displays_filename_and_dimensions() -> None:
    admin_instance = ImageVariantAdmin(ImageVariant, AdminSite())
    variant = ImageVariant(file="images/card/example.webp", width=320, height=332)
    variant.admin_order_number = 7

    assert admin_instance.order_number(variant) == 7
    assert admin_instance.filename(variant) == "example.webp"
    assert admin_instance.dimensions(variant) == "320 x 332"


def test_image_variant_admin_detail_file_links_to_signed_media_url() -> None:
    admin_instance = ImageVariantAdmin(ImageVariant, AdminSite())
    variant = ImageVariant(file="images/card/example.webp", width=320, height=332)

    html = str(admin_instance.secure_file(variant))

    assert f"/v1/admin/media/core/imagevariant/{variant.pk}/file/" in html
    assert "?s=" in html
    assert "&amp;e=" in html


@pytest.mark.django_db
def test_image_variant_admin_numbers_oldest_first_while_showing_newest_first() -> None:
    admin_instance = ImageVariantAdmin(ImageVariant, AdminSite())
    content_type = ContentType.objects.get_for_model(ImageVariant)
    owner_id = uuid.uuid4()
    older = ImageVariant.objects.create(
        content_type=content_type,
        object_id=owner_id,
        role="card",
        width=320,
        height=332,
        mime_type="image/webp",
        file="images/card/older.webp",
    )
    newer = ImageVariant.objects.create(
        content_type=content_type,
        object_id=owner_id,
        role="card",
        width=560,
        height=581,
        mime_type="image/webp",
        file="images/card/newer.webp",
    )
    now = timezone.now()
    ImageVariant.objects.filter(pk=older.pk).update(created_at=now - timedelta(days=1))
    ImageVariant.objects.filter(pk=newer.pk).update(created_at=now)

    rows = list(
        admin_instance.get_queryset(request=None)
        .filter(pk__in=(older.pk, newer.pk))
        .order_by(*admin_instance.ordering)
    )

    assert [(row.pk, row.admin_order_number) for row in rows] == [
        (newer.pk, 2),
        (older.pk, 1),
    ]


@pytest.mark.django_db
def test_image_variant_admin_can_filter_by_astroimage() -> None:
    admin_instance = ImageVariantAdmin(ImageVariant, AdminSite())
    request = RequestFactory().get("/")
    with patch("core.models.process_image_task.delay_on_commit"):
        selected_image = AstroImageFactory(name="Selected image")
        other_image = AstroImageFactory(name="Other image")
    request.GET = request.GET.copy()
    request.GET["astroimage"] = str(selected_image.pk)
    selected_variant = ImageVariant.objects.create(
        image=selected_image,
        role="card",
        width=320,
        height=332,
        mime_type="image/webp",
        file="images/card/selected.webp",
    )
    ImageVariant.objects.create(
        image=other_image,
        role="card",
        width=320,
        height=332,
        mime_type="image/webp",
        file="images/card/other.webp",
    )

    queryset = admin_instance.get_queryset(request)

    assert list(queryset) == [selected_variant]


@pytest.mark.django_db
def test_image_variant_admin_uses_search_widget_for_astroimage_filter() -> None:
    form = ImageVariantAstroImageFilterForm(admin_site=AdminSite())
    widget = form.fields["astroimage"].widget

    assert isinstance(widget, ThemedModelSelect2Widget)
    assert widget.attrs["data-placeholder"] == "Search AstroImage..."
    assert widget.model._meta.label == "astrophotography.AstroImage"
    assert "translations__name__icontains" in widget.search_fields
    assert "slug__icontains" in widget.search_fields


@pytest.mark.django_db
def test_image_variant_admin_changelist_renders_astroimage_search_widget(admin_client) -> None:
    response = admin_client.get(reverse("admin:core_imagevariant_changelist"))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    soup = BeautifulSoup(response.content, "html.parser")
    select = soup.select_one("#id_astroimage")
    search_form = soup.select_one("#changelist-search")

    assert select is not None
    assert search_form is not None
    assert soup.select_one('label[for="id_astroimage"]') is None
    assert soup.select_one("#searchbar") is None
    assert len(search_form.select("select")) == 4
    assert "django-select2-heavy" in select.get("class", [])
    assert "themed-select2" in select.get("class", [])
    assert select["data-ajax--url"] == "/select2/fields/auto.json"
    assert len(select.select("option")) == 1
    assert content.index("vendor/select2/js/select2.min.js") < content.index(
        "django_select2/django_select2.js"
    )


@pytest.mark.django_db
def test_image_variant_admin_changelist_accepts_astroimage_search_filter(admin_client) -> None:
    selected_image = AstroImageFactory(name="Selected image")
    other_image = AstroImageFactory(name="Other image")
    ImageVariant.objects.create(
        image=selected_image,
        role="card",
        width=320,
        height=332,
        mime_type="image/webp",
        file="images/card/selected.webp",
    )
    ImageVariant.objects.create(
        image=other_image,
        role="card",
        width=320,
        height=332,
        mime_type="image/webp",
        file="images/card/other.webp",
    )

    response = admin_client.get(
        reverse("admin:core_imagevariant_changelist"),
        {"astroimage": str(selected_image.pk)},
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "selected.webp" in content
    assert "other.webp" not in content
