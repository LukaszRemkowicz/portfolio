import os
from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import URLPattern, path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from common.utils.signing import generate_signed_url_params

from .log_sources import LOG_SOURCES
from .models import LogAnalysis, SitemapAnalysis
from .tasks import daily_sitemap_analysis_task


def _build_raw_log_fields() -> tuple[str, ...]:
    fields: list[str] = []
    for source in LOG_SOURCES:
        fields.extend(
            [
                f"secure_{source.key}_logs",
                f"server_{source.key}_log_path",
            ]
        )
    fields.append("log_size_bytes")
    return tuple(fields)


@admin.register(LogAnalysis)
class LogAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        "analysis_date",
        "severity",
        "log_size_kb",
        "execution_time_seconds",
        "email_sent",
        "created_at",
    ]
    list_filter = ["severity", "email_sent", "analysis_date"]
    search_fields = ["summary", "recommendations"]
    readonly_fields = [
        "created_at",
        "analysis_date",
        "log_size_bytes",
        "execution_time_seconds",
        "gpt_tokens_used",
        *[
            field
            for source in LOG_SOURCES
            for field in (f"secure_{source.key}_logs", f"server_{source.key}_log_path")
        ],
    ]

    fieldsets = (
        ("Metadata", {"fields": ("created_at", "analysis_date", "severity")}),
        ("Analysis Results", {"fields": ("summary", "key_findings", "recommendations")}),
        (
            "Raw Logs",
            {
                "fields": _build_raw_log_fields(),
                "classes": ("collapse",),
            },
        ),
        (
            "Execution Details",
            {
                "fields": (
                    "execution_time_seconds",
                    "gpt_tokens_used",
                    "email_sent",
                    "error_message",
                )
            },
        ),
    )

    def _secure_log_field(self, obj, field_name: str):
        field_file = getattr(obj, field_name)
        if field_file:
            filename = os.path.basename(field_file.name)
            url = reverse(
                "admin-loganalysis-secure-media",
                kwargs={"pk": str(obj.pk), "field_name": field_name},
            )
            sig_id = (
                f"admin_media_{obj._meta.app_label}_{obj._meta.model_name}_{obj.pk}_{field_name}"
            )
            params = generate_signed_url_params(sig_id, 3600)
            full_url = f"{url}?{urlencode(params)}"

            return format_html('<a href="{}" target="_blank">Download {}</a>', full_url, filename)
        return "-"

    def _server_log_path(self, obj, field_name: str):
        field_file = getattr(obj, field_name)
        if field_file:
            try:
                return str(field_file.path).replace("/app/", "backend/")
            except NotImplementedError:
                return "Not supported by storage backend"
        return "-"

    @admin.display(description="Log Size")
    def log_size_kb(self, obj):
        return f"{obj.log_size_bytes / 1024:.1f} KB"


def _make_secure_log_method(source_key: str, field_name: str):
    @admin.display(description=f"{source_key.title()} Logs")
    def _method(self, obj):
        return self._secure_log_field(obj, field_name)

    return _method


def _make_server_log_path_method(source_key: str, field_name: str):
    @admin.display(description=f"{source_key.title()} Server Path")
    def _method(self, obj):
        return self._server_log_path(obj, field_name)

    return _method


for _source in LOG_SOURCES:
    setattr(
        LogAnalysisAdmin,
        f"secure_{_source.key}_logs",
        _make_secure_log_method(_source.key, _source.model_field),
    )
    setattr(
        LogAnalysisAdmin,
        f"server_{_source.key}_log_path",
        _make_server_log_path_method(_source.key, _source.model_field),
    )


@admin.register(SitemapAnalysis)
class SitemapAnalysisAdmin(admin.ModelAdmin):
    SESSION_TASK_ID_KEY = "monitoring_sitemap_task_id"
    change_list_template = "admin/monitoring/sitemapanalysis/change_list.html"
    list_display = [
        "analysis_date",
        "severity",
        "issue_count",
        "total_sitemaps",
        "total_urls",
        "execution_time_seconds_pretty",
        "email_sent",
        "created_at",
    ]
    list_filter = ["severity", "email_sent", "analysis_date"]
    search_fields = ["summary", "recommendations", "root_sitemap_url"]
    readonly_fields = [
        "created_at",
        "analysis_date",
        "root_sitemap_url",
        "total_sitemaps",
        "total_urls",
        "issue_count",
        "issue_summary_pretty",
        "issue_summary",
        "issues",
        "execution_time_seconds",
        "gpt_tokens_used",
        "gpt_cost_usd",
    ]
    fieldsets = (
        ("Metadata", {"fields": ("created_at", "analysis_date", "severity")}),
        (
            "Sitemap Scope",
            {"fields": ("root_sitemap_url", "total_sitemaps", "total_urls", "issue_count")},
        ),
        ("Analysis Results", {"fields": ("summary", "key_findings", "recommendations")}),
        (
            "Deterministic Findings",
            {
                "fields": ("issue_summary_pretty", "issue_summary", "issues"),
                "classes": ("collapse",),
            },
        ),
        (
            "Execution Details",
            {
                "fields": (
                    "execution_time_seconds",
                    "gpt_tokens_used",
                    "gpt_cost_usd",
                    "email_sent",
                    "error_message",
                )
            },
        ),
    )

    @admin.display(description=_("Issue Count"))
    def issue_count(self, obj: SitemapAnalysis) -> int:
        return obj.issue_count

    @admin.display(description=_("Issue Summary"))
    def issue_summary_pretty(self, obj: SitemapAnalysis) -> str:
        return "\n".join(obj.issue_summary_lines) or "-"

    @admin.display(description=_("Execution time seconds"), ordering="execution_time_seconds")
    def execution_time_seconds_pretty(self, obj: SitemapAnalysis) -> str:
        return f"{obj.execution_time_seconds:.2f}"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def get_urls(self) -> list[URLPattern]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "run-now/",
                self.admin_site.admin_view(self.run_sitemap_analysis_now_view),
                name="monitoring_sitemapanalysis_run_now",
            )
        ]
        return custom_urls + urls

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, object] | None = None
    ) -> HttpResponse:
        context: dict[str, object] = extra_context or {}
        today = timezone.localdate()
        context["run_sitemap_analysis_now_url"] = reverse(
            "admin:monitoring_sitemapanalysis_run_now"
        )
        context["sitemap_task_id"] = str(request.session.pop(self.SESSION_TASK_ID_KEY, ""))
        context["sitemap_task_status_url_template"] = reverse(
            "admin-sitemap-analysis-task-status",
            kwargs={"task_id": "__TASK_ID__"},
        )
        context["today"] = today
        context["last_7_days"] = today - timedelta(days=7)
        context["first_day_of_month"] = today.replace(day=1)
        context["first_day_of_year"] = today.replace(month=1, day=1)
        return super().changelist_view(request, extra_context=context)

    def run_sitemap_analysis_now_view(self, request: HttpRequest) -> HttpResponseRedirect:
        if request.method != "POST":
            changelist_url = reverse("admin:monitoring_sitemapanalysis_changelist")
            return redirect(changelist_url)

        analysis_date = timezone.localdate().isoformat()
        task_result = daily_sitemap_analysis_task.delay(analysis_date=analysis_date)
        self.message_user(
            request,
            _("Queued sitemap analysis run for today."),
            level=messages.SUCCESS,
        )
        request.session[self.SESSION_TASK_ID_KEY] = task_result.id
        return redirect("admin:monitoring_sitemapanalysis_changelist")
