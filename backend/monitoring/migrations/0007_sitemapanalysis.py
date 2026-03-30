import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0006_loganalysis_traefik_logs"),
    ]

    operations = [
        migrations.CreateModel(
            name="SitemapAnalysis",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                ("analysis_date", models.DateField(db_index=True, unique=True)),
                ("root_sitemap_url", models.URLField()),
                ("total_sitemaps", models.IntegerField(default=0)),
                ("total_urls", models.IntegerField(default=0)),
                (
                    "issue_summary",
                    models.JSONField(default=dict, help_text="Counts by sitemap issue category"),
                ),
                (
                    "issues",
                    models.JSONField(
                        default=list, help_text="Detailed deterministic sitemap issues"
                    ),
                ),
                ("summary", models.TextField(help_text="LLM-generated sitemap summary")),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("INFO", "Info"),
                            ("WARNING", "Warning"),
                            ("CRITICAL", "Critical"),
                        ],
                        default="INFO",
                        max_length=10,
                    ),
                ),
                (
                    "key_findings",
                    models.JSONField(default=list, help_text="List of important sitemap findings"),
                ),
                ("recommendations", models.TextField(blank=True, help_text="LLM recommendations")),
                (
                    "trend_summary",
                    models.TextField(blank=True, help_text="Sitemap trend comparison summary"),
                ),
                ("execution_time_seconds", models.FloatField(default=0.0)),
                ("gpt_tokens_used", models.IntegerField(default=0)),
                (
                    "gpt_cost_usd",
                    models.FloatField(default=0.0, help_text="Estimated OpenAI API cost in USD"),
                ),
                ("email_sent", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Sitemap Analysis",
                "verbose_name_plural": "Sitemap Analyses",
                "ordering": ["-analysis_date"],
            },
        ),
    ]
