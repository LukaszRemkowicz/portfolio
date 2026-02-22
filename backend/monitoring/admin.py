from django.contrib import admin

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
    ]

    fieldsets = (
        ("Metadata", {"fields": ("created_at", "analysis_date", "severity")}),
        ("Analysis Results", {"fields": ("summary", "key_findings", "recommendations")}),
        (
            "Raw Logs",
            {
                "fields": ("backend_logs", "frontend_logs", "log_size_bytes"),
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

    @admin.display(description="Log Size")
    def log_size_kb(self, obj):
        return f"{obj.log_size_bytes / 1024:.1f} KB"
