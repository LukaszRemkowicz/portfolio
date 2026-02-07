from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("astrophotography", "0002_refactor_tag_data"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- 1. Drop the redundant slug column from the master Tag table
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'astrophotography_tag' AND column_name = 'slug') THEN
                    -- Drop constraint first if it exists
                    ALTER TABLE astrophotography_tag DROP CONSTRAINT IF EXISTS astrophotography_tag_slug_key;
                    ALTER TABLE astrophotography_tag DROP COLUMN slug;
                END IF;
            END $$;

            -- 2. Ensure Slug in Translation table is NOT NULL
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'astrophotography_tag_translation' AND column_name = 'slug') THEN
                    ALTER TABLE astrophotography_tag_translation ALTER COLUMN slug SET NOT NULL;
                END IF;
            END $$;
            """,
            reverse_sql="SELECT 1;",
        ),
    ]
