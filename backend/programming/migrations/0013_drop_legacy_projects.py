from django.db import migrations


class Migration(migrations.Migration):
    """Drop the pre-translation project tables (production holds no rows).

    Project is recreated as a parler translatable model in the next migration; the historical
    model state cannot be converted in place because parler needs TranslatableModelMixin bases.
    """

    dependencies = [
        ("programming", "0012_remove_baseimage_thumbnail_field"),
    ]

    operations = [
        migrations.DeleteModel(name="ProjectImageTranslation"),
        migrations.DeleteModel(name="ProjectImage"),
        migrations.DeleteModel(name="Project"),
    ]
