from datetime import date

from bs4 import BeautifulSoup

import core.widgets as core_widgets


def test_themed_admin_date_widget_renders_a_generic_library_hook() -> None:
    widget_class = getattr(core_widgets, "ThemedAdminDateWidget", None)
    assert widget_class is not None

    widget = widget_class()
    rendered = widget.render(
        "published_on",
        date(2026, 7, 29),
        attrs={"id": "id_published_on"},
    )
    document = BeautifulSoup(rendered, "html.parser")
    root = document.select_one('[data-themed-date-widget="true"]')
    input_element = document.find("input")
    trigger = document.select_one('[data-date-action="toggle"]')

    assert root is not None
    assert input_element is not None
    assert input_element.get("class") == ["themed-date-widget__input"]
    assert input_element.has_attr("data-air-datepicker")
    assert input_element.get("type") == "text"
    assert input_element.get("value") == "2026-07-29"
    assert trigger is not None
    assert trigger.get("aria-controls") == "id_published_on"
    assert trigger.get("aria-expanded") == "false"
    assert document.select_one("select") is None
    assert document.select_one('[data-date-popup="true"]') is None
    assert "capture_date" not in rendered
    assert widget.media._css == {
        "all": [
            "core/vendor/air-datepicker/3.6.0/air-datepicker.css",
            "core/css/themed_date_widget_v3.css",
        ],
    }
    assert widget.media._js == [
        "core/vendor/air-datepicker/3.6.0/air-datepicker.js",
        "core/js/themed_date_widget_v3.js",
    ]
