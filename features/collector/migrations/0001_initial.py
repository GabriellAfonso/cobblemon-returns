from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CollectionLog",
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
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("ok", "OK"), ("error", "Error")],
                        max_length=10,
                    ),
                ),
                ("message", models.TextField(blank=True)),
                ("players_updated", models.IntegerField(default=0)),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
    ]
