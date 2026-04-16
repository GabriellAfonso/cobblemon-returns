import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Player",
            fields=[
                (
                    "uuid",
                    models.CharField(max_length=36, primary_key=True, serialize=False),
                ),
                ("username", models.CharField(max_length=32)),
                ("last_seen", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="PlayerStats",
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
                ("play_time_ticks", models.BigIntegerField(default=0)),
                ("pokemons_caught", models.IntegerField(default=0)),
                ("pokedex_registered", models.IntegerField(default=0)),
                ("cobbletcg_cards", models.IntegerField(default=0)),
                ("battles_won", models.IntegerField(default=0)),
                ("cobbledollars", models.IntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "player",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stats",
                        to="players.player",
                    ),
                ),
            ],
        ),
    ]
