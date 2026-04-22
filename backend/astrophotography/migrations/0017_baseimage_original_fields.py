from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("astrophotography", "0016_astroimage_calculated_exposure_hours"),
    ]

    operations = [
        migrations.AddField(
            model_name="astroimage",
            name="original",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Canonical uploaded source image for the next BaseImage contract.",
                null=True,
                upload_to="images/",
                verbose_name="Original Image Source",
            ),
        ),
        migrations.AddField(
            model_name="astroimage",
            name="original_webp",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Derived WebP image for the next BaseImage contract.",
                null=True,
                upload_to="images/",
                verbose_name="Original Image WebP",
            ),
        ),
        migrations.AddField(
            model_name="mainpagebackgroundimage",
            name="original",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Canonical uploaded source image for the next BaseImage contract.",
                null=True,
                upload_to="images/",
                verbose_name="Original Image Source",
            ),
        ),
        migrations.AddField(
            model_name="mainpagebackgroundimage",
            name="original_webp",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Derived WebP image for the next BaseImage contract.",
                null=True,
                upload_to="images/",
                verbose_name="Original Image WebP",
            ),
        ),
    ]
