from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monitoring", "0005_loganalysis_trend_summary"),
    ]

    operations = [
        migrations.AddField(
            model_name="loganalysis",
            name="traefik_logs",
            field=models.FileField(
                blank=True,
                help_text="Raw traefik logs",
                null=True,
                upload_to="logs/%Y/%m/%d/",
            ),
        ),
    ]
