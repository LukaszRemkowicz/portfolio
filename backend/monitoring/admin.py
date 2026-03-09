import os

from django.contrib import admin
from django.utils.html import format_html

from .models import LogAnalysis


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
        "secure_backend_logs",
        "server_backend_log_path",
        "secure_frontend_logs",
        "server_frontend_log_path",
        "secure_nginx_logs",
        "server_nginx_log_path",
    ]

    fieldsets = (
        ("Metadata", {"fields": ("created_at", "analysis_date", "severity")}),
        ("Analysis Results", {"fields": ("summary", "key_findings", "recommendations")}),
        (
            "Raw Logs",
            {
                "fields": (
                    "secure_backend_logs",
                    "server_backend_log_path",
                    "secure_frontend_logs",
                    "server_frontend_log_path",
                    "secure_nginx_logs",
                    "server_nginx_log_path",
                    "log_size_bytes",
                ),
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

    @admin.display(description="Backend Logs")
    def secure_backend_logs(self, obj):
        if obj.backend_logs:
            from urllib.parse import urlencode

            from django.urls import reverse

            from common.utils.signing import generate_signed_url_params

            filename = os.path.basename(obj.backend_logs.name)
            url = reverse(
                "admin-loganalysis-secure-media",
                kwargs={"pk": str(obj.pk), "field_name": "backend_logs"},
            )
            sig_id = (
                f"admin_media_{obj._meta.app_label}_{obj._meta.model_name}_{obj.pk}_backend_logs"
            )
            params = generate_signed_url_params(sig_id, 3600)
            full_url = f"{url}?{urlencode(params)}"

            return format_html('<a href="{}" target="_blank">Download {}</a>', full_url, filename)
        return "-"

    @admin.display(description="Frontend Logs")
    def secure_frontend_logs(self, obj):
        if obj.frontend_logs:
            from urllib.parse import urlencode

            from django.urls import reverse

            from common.utils.signing import generate_signed_url_params

            filename = os.path.basename(obj.frontend_logs.name)
            url = reverse(
                "admin-loganalysis-secure-media",
                kwargs={"pk": str(obj.pk), "field_name": "frontend_logs"},
            )
            sig_id = (
                f"admin_media_{obj._meta.app_label}_{obj._meta.model_name}_{obj.pk}_frontend_logs"
            )
            params = generate_signed_url_params(sig_id, 3600)
            full_url = f"{url}?{urlencode(params)}"

            return format_html('<a href="{}" target="_blank">Download {}</a>', full_url, filename)
        return "-"

    @admin.display(description="Nginx Logs")
    def secure_nginx_logs(self, obj):
        if obj.nginx_logs:
            from urllib.parse import urlencode

            from django.urls import reverse

            from common.utils.signing import generate_signed_url_params

            filename = os.path.basename(obj.nginx_logs.name)
            url = reverse(
                "admin-loganalysis-secure-media",
                kwargs={"pk": str(obj.pk), "field_name": "nginx_logs"},
            )
            sig_id = f"admin_media_{obj._meta.app_label}_{obj._meta.model_name}_{obj.pk}_nginx_logs"
            params = generate_signed_url_params(sig_id, 3600)
            full_url = f"{url}?{urlencode(params)}"

            return format_html('<a href="{}" target="_blank">Download {}</a>', full_url, filename)
        return "-"

    @admin.display(description="Backend Server Path")
    def server_backend_log_path(self, obj):
        if obj.backend_logs:
            try:
                # Translate container-internal /app/... to host-relative backend/...
                return str(obj.backend_logs.path).replace("/app/", "backend/")
            except NotImplementedError:
                return "Not supported by storage backend"
        return "-"

    @admin.display(description="Frontend Server Path")
    def server_frontend_log_path(self, obj):
        if obj.frontend_logs:
            try:
                return str(obj.frontend_logs.path).replace("/app/", "backend/")
            except NotImplementedError:
                return "Not supported by storage backend"
        return "-"

    @admin.display(description="Nginx Server Path")
    def server_nginx_log_path(self, obj):
        if obj.nginx_logs:
            try:
                return str(obj.nginx_logs.path).replace("/app/", "backend/")
            except NotImplementedError:
                return "Not supported by storage backend"
        return "-"

    @admin.display(description="Log Size")
    def log_size_kb(self, obj):
        return f"{obj.log_size_bytes / 1024:.1f} KB"
