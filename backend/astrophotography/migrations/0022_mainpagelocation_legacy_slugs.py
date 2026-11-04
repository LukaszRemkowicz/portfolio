from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("astrophotography", "0021_remove_baseimage_thumbnail_fields")]

    operations = [
        migrations.AddField(
            model_name="mainpagelocation",
            name="legacy_slugs",
            field=models.JSONField(blank=True, default=list, editable=False),
        ),
    ]
