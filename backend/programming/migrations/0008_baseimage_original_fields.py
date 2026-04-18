from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("programming", "0007_alter_projectimage_original_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectimage",
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
            model_name="projectimage",
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
