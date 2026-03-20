from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("astrophotography", "0013_alter_astroimage_legacy_path_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="astroimage",
            old_name="legacy_path",
            new_name="original_image",
        ),
        migrations.RenameField(
            model_name="mainpagebackgroundimage",
            old_name="legacy_path",
            new_name="original_image",
        ),
        migrations.AlterField(
            model_name="astroimage",
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
        migrations.AlterField(
            model_name="mainpagebackgroundimage",
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
