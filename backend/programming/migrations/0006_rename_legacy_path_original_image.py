from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("programming", "0005_alter_projectimage_legacy_path"),
    ]

    operations = [
        migrations.RenameField(
            model_name="projectimage",
            old_name="legacy_path",
            new_name="original_image",
        ),
        migrations.AlterField(
            model_name="projectimage",
            name="original_image",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Original file path before WebP conversion. Used for rollback via the Admin serve_webp_images toggle. TODO:Will be removed in future versions.",
                null=True,
                upload_to="images/",
                verbose_name="Original Image",
            ),
        ),
    ]
