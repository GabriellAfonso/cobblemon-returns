from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mods", "0002_alter_mod_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="mod",
            name="modrinth_id",
            field=models.CharField(blank=True, db_index=True, max_length=20),
        ),
        migrations.CreateModel(
            name="PackwizSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Packwiz Snapshot",
                "verbose_name_plural": "Packwiz Snapshot",
            },
        ),
    ]
